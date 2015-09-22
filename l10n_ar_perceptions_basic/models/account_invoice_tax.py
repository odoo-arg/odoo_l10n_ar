# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning


class AccountInvoiceTax(models.Model):

    _inherit = "account.invoice.tax"

    #~ SE AGREGAN LOS IMPUESTOS A LA FACTURA PERTENECIENTES A LA PERCEPCION.
    @api.v8
    def hook_compute_invoice_taxes(self, invoice, tax_grouped):

        auto = self.env.context.get('auto', False)

        if auto:
            return super(AccountInvoiceTax, self).hook_compute_invoice_taxes(invoice, tax_grouped)

        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))

        #~ SE COMPUTAN LAS PERCEPCIONES COMO IMPUESTOS
        for line in invoice.perception_ids:
            val = {}
            tax = line.perception_id.tax_id
            val['invoice_id'] = invoice.id
            val['name'] = line.name
            val['amount'] = line.amount
            val['manual'] = False
            val['sequence'] = 10
            val['is_exempt'] = False
            val['base'] = line.base
            val['tax_id'] = tax.id

            #~ CALCULO DE TAX AMOUNT Y BASE AMOUNT
            tax_amount, base_amount = line._compute(invoice, val['base'], val['amount'])

            if invoice.type in ('out_invoice', 'in_invoice'):
                val['base_code_id'] = line.base_code_id.id
                val['tax_code_id'] = line.tax_code_id.id
                val['base_amount'] = base_amount
                val['tax_amount'] = tax_amount
                val['account_id'] = tax.account_collected_id.id
                val['account_analytic_id'] = tax.account_analytic_collected_id.id
            else:
                val['base_code_id'] = tax.ref_base_code_id.id
                val['tax_code_id'] = tax.ref_tax_code_id.id
                val['base_amount'] = base_amount
                val['tax_amount'] = tax_amount
                val['account_id'] = tax.account_paid_id.id
                val['account_analytic_id'] = tax.account_analytic_paid_id.id

            key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
            if not key in tax_grouped:
                tax_grouped[key] = val
            else:
                tax_grouped[key]['amount'] += val['amount']
                tax_grouped[key]['base'] += val['base']
                tax_grouped[key]['base_amount'] += val['base_amount']
                tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])

        return super(AccountInvoiceTax, self).hook_compute_invoice_taxes(invoice, tax_grouped)

AccountInvoiceTax()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
