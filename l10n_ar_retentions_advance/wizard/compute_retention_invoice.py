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

class ComputeRetentionInvoice(models.TransientModel):

    _name = 'compute.retention.invoice'

    invoice_id = fields.Many2one('account.invoice', 'Factura', readonly=True)
    compute_retention_wizard_id = fields.Many2one('compute.retention.wizard', 'wizard')
    type_analysis = fields.Selection(related='invoice_id.type_analysis', string='Tipo')
    date = fields.Date(related='invoice_id.date_invoice', string='Fecha')
    name = fields.Char(related='invoice_id.internal_number', string='Numero')
    balance = fields.Float(related='invoice_id.residual', string='Balance')
    subtotal = fields.Float(related='invoice_id.amount_untaxed', string='Subtotal')
    total = fields.Float(related='invoice_id.amount_total', string='Total')
    amount = fields.Float('Importe a pagar con retenciones')
    amount_of_retentions = fields.Float('Total de retenciones')         
    amount_to_pay = fields.Float('Total de valores')
    currency_id = fields.Many2one('res.currency', 'Moneda')
    cotization = fields.Float('Cotizacion')
    
    @api.onchange('amount', 'amount_to_pay')
    def onchange_amount(self):
        
        if self.invoice_id.residual < self.amount or self.amount < 0.0:
             
            self.amount = self.invoice_id.residual 
         
            return{
 
                'warning': {'title': 'Error!', 'message': 'Importe invalido'}
            }

ComputeRetentionInvoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: