# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
from openerp.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.depends('name')
    def _set_has_number(self):

        default_name = self.default_get(['name']).get('name')

        # Si tiene un punto de venta al momento de setear el nombre, ya no se deberia poder editar nuevamente
        for payment in self:
            payment.has_number = True if payment.name and payment.name != default_name else False

    def _get_default_pos(self):

        default_type = self.default_get(['payment_type']).get('payment_type')
        pos = None
        if default_type:
            pos = self.env['document.book'].search([
                ('category', '=', 'payment'),
                ('document_type_id.type', '=', default_type)],
                limit=1,
                order="sequence asc",
            ).pos_ar_id.id

        return pos

    pos_ar_id = fields.Many2one(
        'pos.ar',
        'Punto de venta',
        default=_get_default_pos
    )
    has_number = fields.Boolean('Tiene numero pos', compute='_set_has_number')

    def _get_liquidity_move_line_vals(self, amount):
        """
        Usamos los talonarios para el nombre de los recibos, ordenes de pagos y lineas de asientos
        """
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)

        if self.pos_ar_id:

            # Orden de pago y recibo
            if (self.payment_type == 'outbound' and self.partner_type == 'supplier') \
                    or (self.payment_type == 'inbound' and self.partner_type == 'customer'):

                prefix = 'REC ' if self.payment_type == 'inbound' else 'OP '
                old_names = self.env.context.get('old_names')
                payment_old_name_ids = [old_name_id for old_name_id in old_names] if old_names else []

                # Si por contexto tenemos old_name, significa que es un pago que se cancelo y se re-valido
                # en ese caso mantenemos el mismo nombre, si no, le pedimos al talonario
                name = old_names.get(self.id) if self.id in payment_old_name_ids else \
                    self.get_document_book().next_number()

                self.name = name
                vals['name'] = prefix+name

                # Hay dos casos mas, ordenes de pago a clientes y recibos a proveedores, por ahora
                # no los contemplamos ya que no tienen uso.

        return vals

    @api.multi
    def post(self):
        """ Mantenemos el nombre viejo para los casos que se re-validen pagos/cobros cancelados """

        default_name = self.default_get(['name']).get('name')

        # Si existe nombre y no es el default, le ponemos al contexto su id y nombre viejo
        old_names = {rec.id: rec.name for rec in self if rec.name and rec.name != default_name}

        self = self.with_context(old_names=old_names)

        super(AccountPayment, self).post()

    def get_document_book(self):
        """
        Busca el talonario predeterminado para el tipo de pago
        :return: Talonario a utilizar
        :raise UserError: No hay configurado un talonario para ese punto de venta y tipo de comprobante
        """
        self.ensure_one()

        domain = ([
            ('pos_ar_id', '=', self.pos_ar_id.id),
            ('category', '=', 'payment'),
            ('document_type_id.type', '=', self.payment_type)
        ])

        document_book = self.env['document.book'].search(domain, limit=1)
        if not document_book:
            raise ValidationError(
                'No existe talonario configurado para el punto de venta ' + self.pos_ar_id.name_get()[0][1]
            )

        return document_book

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
