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


class PerceptionTaxLine(models.Model):

    _name = "perception.tax.line"

    _description = "Linea Impuesto Percepcion"

    _order = "date desc"

    @api.one
    @api.depends('amount')
    def _get_amount_with_sign(self):
        if self.invoice_id.type in ['in_invoice','out_refund']:
            self.amount_with_sign = - self.amount
        else:
            self.amount_with_sign = self.amount


    name = fields.Char(string="Nombre", required=True)

    date = fields.Date(string="Fecha")

    invoice_id = fields.Many2one("account.invoice",string="Factura",ondelete="cascade",)

    account_id = fields.Many2one("account.account", string="Cuenta Impuesto", required=True, domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')],)

    base = fields.Float(string="Base", digits_compute=dp.get_precision("Account"), required=True)

    amount = fields.Float(string="Monto", digits_compute=dp.get_precision("Account"), required=True)

    amount_with_sign = fields.Float(string="Monto", compute="_get_amount_with_sign")

    perception_id = fields.Many2one("perception.perception", string="Percepcion", required=True,)

    type = fields.Selection(related="perception_id.type", string="Tipo Percepcion", readonly=True, store=True)

    state_id = fields.Many2one(related="perception_id.state_id", string="Provincia", readonly=True, store=True)

    jurisdiccion = fields.Selection(related="perception_id.jurisdiccion", string="Jurisdiccion", readonly=True, store=True)

    base_code_id = fields.Many2one("account.tax.code", string="Cuenta Base",)

    base_amount = fields.Float(string="Monto Base", digits_compute=dp.get_precision("Account"),)

    tax_code_id = fields.Many2one("account.tax.code", string="Cuenta Impuesto",)

    tax_amount = fields.Float(string="Monto Impuesto", digits_compute=dp.get_precision("Account"),)

    company_id = fields.Many2one(related="account_id.company_id", string="Empresa", store=True, readonly=True)

    partner_id = fields.Many2one(related="invoice_id.partner_id", string="Tercero", readonly=True)

    vat = fields.Char(related="invoice_id.partner_id.vat", string="CUIT/CUIL", readonly=True, store=True)

    ait_id = fields.Many2one("account.invoice.tax", "Impuesto Factura", ondelete="cascade")

    @api.one
    @api.constrains('amount', 'base')
    def _check_amounts(self):

        if self.amount <= 0 or self.base < 0 or self.base < self.amount:

            raise Warning("Importe erroneo en alguna linea de percepcion.")


    @api.one
    @api.onchange('perception_id')
    def onchange_perception(self):

        if not self.perception_id:

            self.name = False
            self.account_id = False
            self.base_code_id = False
            self.tax_code_id = False

        else:

            self.name = self.perception_id.name
            self.account_id = self.perception_id.tax_id.account_collected_id.id
            self.base_code_id = self.perception_id.tax_id.base_code_id.id
            self.tax_code_id = self.perception_id.tax_id.tax_code_id.id


    @api.v8
    def _compute(self, invoice, base, amount):

        tax = self.perception_id.tax_id

        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))

        company_currency = invoice.company_id.currency_id

        base_amount = currency.compute(base * tax.base_sign, company_currency, round=False)

        tax_amount = currency.compute(amount * tax.tax_sign, company_currency, round=False)

        return (tax_amount, base_amount)


PerceptionTaxLine()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
