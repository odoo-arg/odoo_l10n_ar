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
from openerp.addons import decimal_precision as dp
from openerp.exceptions import Warning
import time


class RetentionTaxLine(models.Model):

    _name = "retention.tax.line"

    _description = "Linea Impuesto Retencion"

    _order = "date desc"

    @api.one
    @api.depends('amount')
    def _get_amount_with_sign(self):
        if self.retention_id.type_tax_use == 'purchase':
            self.amount_with_sign = - self.amount
        else:
            self.amount_with_sign = self.amount


    name = fields.Char(string="Nombre", required=True)

    date = fields.Date(string="Fecha")

    voucher_id = fields.Many2one("account.voucher",string="Recibo",ondelete="cascade",)

    voucher_number = fields.Char('Numero Recibo', related="voucher_id.number", readonly=True)

    account_id = fields.Many2one("account.account", string="Cuenta Impuesto", required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')],)

    base = fields.Float(string="Base", digits_compute=dp.get_precision("Account"), required=True)

    amount = fields.Float(string="Monto", digits_compute=dp.get_precision("Account"), required=True)

    amount_with_sign = fields.Float(string="Monto", compute="_get_amount_with_sign")

    retention_id = fields.Many2one("retention.retention", string="Retencion", required=True,)

    type = fields.Selection(related="retention_id.type", string="Tipo Percepcion", readonly=True, store=True)

    state_id = fields.Many2one(related="retention_id.state_id", string="Provincia", readonly=True, store=True)

    jurisdiccion = fields.Selection(related="retention_id.jurisdiccion", string="Jurisdiccion", readonly=True, store=True)

    base_code_id = fields.Many2one("account.tax.code", string="Cuenta Base",)

    base_amount = fields.Float(string="Monto Base", digits_compute=dp.get_precision("Account"),)

    tax_code_id = fields.Many2one("account.tax.code", string="Cuenta Impuesto",)

    tax_amount = fields.Float(string="Monto Impuesto", digits_compute=dp.get_precision("Account"),)

    company_id = fields.Many2one(related="account_id.company_id", string="Empresa", store=True, readonly=True)

    partner_id = fields.Many2one(related="voucher_id.partner_id", string="Tercero", readonly=True)

    vat = fields.Char(related="voucher_id.partner_id.vat", string="CUIT/CUIL", readonly=True, store=True)

    certificate_no = fields.Char("Numero Certificado", required=False)

    regimen = fields.Char("Regimen")

    regimen_code = fields.Integer("Codigo Regimen")


    @api.one
    @api.constrains('amount', 'base')
    def _check_amounts(self):

        if self.amount <= 0 or self.base < 0 or self.base < self.amount:

            raise Warning("Importe erroneo en alguna linea de retencion.")


    @api.one
    @api.onchange('retention_id')
    def onchange_retention(self):

        if not self.retention_id:

            self.name = False
            self.account_id = False
            self.base_code_id = False
            self.tax_code_id = False

        else:

            self.name = self.retention_id.name
            self.account_id = self.retention_id.tax_id.account_collected_id.id
            self.base_code_id = self.retention_id.tax_id.base_code_id.id
            self.tax_code_id = self.retention_id.tax_id.tax_code_id.id



    def create_voucher_move_line(self, cr, uid, retention, voucher, context=None):

        voucher_obj = self.pool.get('account.voucher')

        if retention.amount == 0.0:

            return move_lines

        company_currency = voucher.company_id.currency_id.id

        current_currency = voucher.currency_id.id

        tax_amount_in_company_currency =  voucher_obj._convert_paid_amount_in_company_currency(cr, uid, voucher, retention.amount, context=context)

        base_amount_in_company_currency =  voucher_obj._convert_paid_amount_in_company_currency(cr, uid, voucher, retention.base, context=context)

        debit = 0.0

        credit = 0.0

        if voucher.type in ('purchase', 'payment'):

            credit = tax_amount_in_company_currency

        elif voucher.type in ('sale', 'receipt'):

            debit = tax_amount_in_company_currency

        if debit < 0: credit = -debit; debit = 0.0

        if credit < 0: debit = -credit; credit = 0.0

        sign = debit - credit < 0 and -1 or 1

        move_line = {

            'name': retention.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': retention.account_id.id,
            'tax_code_id': retention.tax_code_id.id,
            'tax_amount': tax_amount_in_company_currency,
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': company_currency <> current_currency and  current_currency or False,
            'amount_currency': company_currency <> current_currency and sign * retention.amount or 0.0,
            'date': voucher.date,
            'date_maturity': voucher.date_due

        }

        return move_line

RetentionTaxLine()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
