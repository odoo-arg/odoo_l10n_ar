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


class AccountInvoicePerception(models.Model):
    """
    Percepciones cargadas en invoices. Tener en cuenta que hay datos necesarios que se deberian tomar
    de la invoice: Cuit, Moneda, Fecha, Tipo (Proveedor/Cliente)
    """

    _inherit = 'account.document.tax'
    _name = 'account.invoice.perception'

    @api.onchange('perception_id')
    def onchange_perception_id(self):
        if self.perception_id:
            self.update({
                'name': self.perception_id.name,
                'jurisdiction': self.perception_id.jurisdiction,
            })
        else:
            self.update({
                'name': None,
                'jurisdiction': None,
            })

    invoice_id = fields.Many2one('account.invoice', 'Documento', required=True)
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    perception_id = fields.Many2one(
        'perception.perception',
        'Percepcion',
        ondelete='restrict',
        required=True
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
