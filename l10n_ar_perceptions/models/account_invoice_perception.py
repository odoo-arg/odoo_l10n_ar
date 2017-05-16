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
import logging
_logger = logging.getLogger(__name__)


class AccountInvoicePerception(models.Model):
    """
    Percepciones cargadas en invoices. Tener en cuenta que hay datos necesarios que se deberian tomar
    de la invoice: Cuit, Moneda, Fecha, Tipo (Proveedor/Cliente)
    """

    _name = 'account.invoice.perception'

    def _get_signed_amount(self):
        for perception in self:
            sign = 1 if perception.invoice_id.type != 'out_refund' else -1
            perception.amount_signed = perception.amount * sign

    @api.onchange('perception_id')
    def onchange_perception_id(self):
        if self.perception_id:
            _logger.info('PONIENDO NAME')
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
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    amount = fields.Monetary('Importe', currency_field='currency_id', required=True)
    amount_signed = fields.Monetary('Importe con signo', currency_field='currency_id', compute='_get_signed_amount')
    base = fields.Monetary('Base', currency_field='currency_id')
    jurisdiction = fields.Selection(
        [
            ('nacional', 'Nacional'),
            ('provincial', 'Provincial'),
            ('municipal', 'Municipal')
        ],
        string='Jurisdiccion',
        required=True,
    )
    name = fields.Char('Nombre', required=True)
    perception_id = fields.Many2one(
        'perception.perception',
        'Percepcion',
        ondelete='restrict',
        required=True
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
