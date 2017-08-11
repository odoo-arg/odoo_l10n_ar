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

import json
from openerp import models, fields, api
from openerp.exceptions import ValidationError


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    """
    Comentario general: Los campos de importes de las facturas tienen el campo replicado con "signed"
    esto significa que muestra los campos en el signo que corresponda (si es nc en negativo, si no positivo).
    Considero que no es necesario hacerlo para estos campos ya que no se suelen utilizar de esa manera.
    """
    # Neto gravado
    amount_to_tax = fields.Monetary(string='Neto gravado', store=True, readonly=True, compute='_compute_amount')
    # No gravado
    amount_not_taxable = fields.Monetary(string='No gravado', store=True, readonly=True, compute='_compute_amount')
    # Exento
    amount_exempt = fields.Monetary(string='Exento', store=True, readonly=True, compute='_compute_amount')
    amounts_widget = fields.Text(compute='_get_amount_info_JSON')

    @api.depends('amount_to_tax', 'amount_not_taxable', 'amount_exempt')
    def _get_amount_info_JSON(self):
        for inv in self:
            info = {'title': 'Informacion de importes', 'outstanding': False, 'content': []}
            info['content'].append({
                'amount_to_tax': inv.amount_to_tax,
                'amount_not_taxable': inv.amount_not_taxable,
                'amount_exempt': inv.amount_exempt,
                'currency': inv.currency_id.symbol,
                'position': inv.currency_id.position,
            })
            inv.amounts_widget = json.dumps(info)

    def _compute_amount(self):

        res = super(AccountInvoice, self)._compute_amount()

        for invoice in self:
            group_vat = self.env.ref('l10n_ar.tax_group_vat', False)
            if not group_vat:
                raise ValidationError('Grupo de impuesto de IVA no encontrado en la configuracion de impuestos')

            amount_exempt = sum(line.base for line in invoice.tax_line_ids
                                if line.tax_id.tax_group_id == group_vat and line.tax_id.is_exempt)
            amount_to_tax = sum(line.base for line in invoice.tax_line_ids
                                if line.tax_id.tax_group_id == group_vat and not line.tax_id.is_exempt)

            # Dejamos como no gravado lo que no esta en el neto gravado ni en el importe exento
            invoice.amount_not_taxable = invoice.amount_untaxed - amount_exempt - amount_to_tax
            invoice.amount_to_tax = amount_to_tax
            invoice.amount_exempt = amount_exempt

        return res

    @api.constrains('invoice_line_ids')
    def check_more_than_one_vat_in_line(self):
        """ Se asegura que no haya mas de un impuesto tipo IVA en las lineas de factura """
        group_vat = self.env.ref('l10n_ar.tax_group_vat')

        for invoice in self:
            for line in invoice.invoice_line_ids:
                if len(line.invoice_line_tax_ids.filtered(lambda r: r.tax_group_id == group_vat)) > 1:
                    raise ValidationError("No puede haber mas de un impuesto de tipo IVA en una linea!")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
