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

from openerp import models, fields, api
from openerp.exceptions import UserError


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    pos_ar_id = fields.Many2one('pos.ar', 'Punto de venta')
    denomination_id = fields.Many2one('account.denomination', 'Denominacion')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Seteamos el punto de venta y la denominacion del talonario mas prioritario
        """

        if self.partner_id:

            denomination = self.get_invoice_denomination()
            document_book = self.env['document.book'].search([
                ('category', '=', 'invoice'),
                ('denomination_id', '=', denomination.id)
            ], order="sequence asc", limit=1)

            self.update({
                'pos_ar_id': document_book.pos_ar_id.id,
                'denomination_id': denomination.id
            })

        else:
            self.update({
                'pos_ar_id': None,
                'denomination_id': None
            })

    def get_invoice_denomination(self):
        """
        Busca la denominacion en base a las posiciones fiscales del partner y la empresa
        """
        issue_fiscal_position = self.get_issue_fiscal_position()
        receipt_fiscal_position = self.get_receipt_fiscal_position()

        denomination = self.denomination_id

        if issue_fiscal_position and receipt_fiscal_position:
            denomination = issue_fiscal_position.get_denomination(receipt_fiscal_position)

        return denomination

    def get_issue_fiscal_position(self):
        """
        :return: Posicion fiscal emisora segun tipo de factura
        """
        company_fiscal_position = self.company_id.partner_id.property_account_position_id
        partner_fiscal_position = self.partner_id.property_account_position_id

        issue_fiscal_position = company_fiscal_position if self.type in ('out_invoice', 'out_refund')\
            else partner_fiscal_position

        return issue_fiscal_position

    def get_receipt_fiscal_position(self):
        """
        :return: Posicion fiscal receptora segun tipo de factura
        """
        company_fiscal_position = self.company_id.partner_id.property_account_position_id
        partner_fiscal_position = self.partner_id.property_account_position_id

        receipt_fiscal_position = partner_fiscal_position if self.type in ('out_invoice', 'out_refund')\
            else company_fiscal_position

        return receipt_fiscal_position

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()

        for invoice in self:
            invoice._validate_fiscal_position_and_denomination()
            invoice.name = invoice._get_next_number()

        return res

    def _validate_fiscal_position_and_denomination(self):
        """
        Valida si las posiciones fiscales de los partnes y la empresa
        van acorde a la denominacion de la factura
        :raises UserError: Si no esta configurada la posicion fiscal de la empresa, partner, o si no es igual
        la posicion fiscal del partner a la de la factura
        :raise UserError: Si la denominacion de la factura no es la correcta segun posiciones fiscales
        """

        # Valido posiciones fiscales
        company_fiscal_position = self.company_id.partner_id.property_account_position_id
        partner_fiscal_position = self.partner_id.property_account_position_id
        self._validate_fiscal_position(company_fiscal_position, partner_fiscal_position)

        # Valido denominacion
        issue_fiscal_position = self.get_issue_fiscal_position()
        receipt_fiscal_position = self.get_receipt_fiscal_position()
        denomination = issue_fiscal_position.get_denomination(receipt_fiscal_position)
        self._validate_denomination(denomination)

    def _validate_fiscal_position(self, company_fiscal_position, partner_fiscal_position):
        """
        Valida las posiciones fiscales de la factura
        :param company_fiscal_position: account.fiscal.position - Posicion fiscal de la empresa
        :param partner_fiscal_position: account.fiscal.position - Posicion fiscal del partner de la factura
        :raises UserError: Si no esta configurada la posicion fiscal de la empresa, partner, o si no es igual
        la posicion fiscal del partner a la de la factura
        """

        if not company_fiscal_position:
            raise UserError('Por favor, configurar la posicion fiscal de la empresa ' + self.company_id.name)
        if not partner_fiscal_position:
            raise UserError('Por favor, configurar la posicion fiscal del partner')

        if self.fiscal_position_id != partner_fiscal_position:
            raise UserError('La posicion fiscal del documento debe ser la misma que la configurada en el partner')

    def _validate_denomination(self, denomination):
        """
        Valida la denominacion de la factura
        :param denomination: account.denomination - Posicion fiscal que deberia tener la factura
        :raise UserError: Si la denominacion de la factura no es la correcta segun posiciones fiscales
        """

        if denomination != self.denomination_id:
            raise UserError('La denominacion de la factura no es la misma que la configurada en las posiciones fiscales')

    def _get_next_number(self):
        """
        Busca el proximo valor del documento en base al talonario obtenido del punto de venta y denominacion
        :return: Numero a utilizar del talonario
        :raise UserError: No esta seteado el punto de venta o la denominacion
        :raise UserError: No hay configurado un talonario para ese punto de venta y denominacion
        """

        if not (self.pos_ar_id and self.denomination_id):
            raise UserError('El documento debe tener punto de venta y denominacion para ser validado')

        document_book = self.env['document.book'].search([
            ('denomination_id', '=', self.denomination_id.id),
            ('pos_ar_id', '=', self.pos_ar_id.id),
            ('category', '=', 'invoice')
        ], limit=1)

        if not document_book:
            raise UserError('No existe talonario configurado para el punto de venta '
                            + self.pos_ar_id.name_get()[0][1] + ' y la denominacion ' + self.denomination_id.name)

        return document_book.next_number()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
