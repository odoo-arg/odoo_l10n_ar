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
from openerp.exceptions import Warning


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    """
    Comentario general: Los campos de improtes de las facturas tienen el campo replicado con "signed"
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
        info = {'title': 'Informacion de importes', 'outstanding': False, 'content': []}
        info['content'].append({
            'amount_to_tax': self.amount_to_tax,
            'amount_not_taxable': self.amount_not_taxable,
            'amount_exempt': self.amount_exempt,
            'currency': self.currency_id.symbol,
            'position': self.currency_id.position,
        })
        self.amounts_widget = json.dumps(info)

    def _compute_amount(self):

        res = super(AccountInvoice, self)._compute_amount()

        for invoice in self:
            group_vat = self.env.ref('l10n_ar.tax_group_vat')
            if not group_vat:
                raise Warning('Grupo de impuesto de IVA no encontrado en la configuracion de impuestos')

            amount_exempt = sum(line.base for line in invoice.tax_line_ids
                                if line.tax_id.tax_group_id == group_vat and line.tax_id.is_exempt)
            amount_to_tax = sum(line.base for line in invoice.tax_line_ids
                                if line.tax_id.tax_group_id == group_vat and not line.tax_id.is_exempt)

            # Dejamos como no gravado lo que no esta en el neto gravado ni en el importe exento
            invoice.amount_not_taxable = invoice.amount_untaxed - amount_exempt - amount_to_tax
            invoice.amount_to_tax = amount_to_tax
            invoice.amount_exempt = amount_exempt

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
