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

from openerp import models, fields


class AccountPaymentImputationWizardLine(models.TransientModel):

    _name = 'payment.imputation.wizard.line'

    invoice_id = fields.Many2one('account.invoice', 'Documento', required=True)
    wizard_id = fields.Many2one('payment.imputation.wizard', 'Wizard')
    wizard_currency_id = fields.Many2one(related='wizard_id.currency_id')
    amount = fields.Monetary('Total A imputar', currency_field='wizard_currency_id')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    company_currency_id = fields.Many2one(related='invoice_id.company_currency_id')
    invoice_amount_residual = fields.Monetary(related='invoice_id.residual_signed')
    invoice_amount_total = fields.Monetary(related='invoice_id.amount_total_signed')
    invoice_amount_residual_company = fields.Monetary(related='invoice_id.residual_company_signed')
    invoice_amount_company = fields.Monetary(related='invoice_id.amount_total_company_signed')
    invoice_name = fields.Char(related='invoice_id.full_name')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
