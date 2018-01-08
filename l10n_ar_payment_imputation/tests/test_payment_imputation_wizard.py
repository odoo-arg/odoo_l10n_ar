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

from odoo.tests import common
from openerp.exceptions import ValidationError


class TestPaymentImputationWizard(common.TransactionCase):

    def _create_invoice(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        product_21_consu = self.env['product.product'].create({
            'name': '21 consu',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.env.ref('l10n_ar.1_vat_21_compras').id])]
        })
        invoice = invoice_proxy.create({
            'partner_id': self.partner.id,
            'type': 'in_invoice',
            'name': '0001-00000001'
        })
        invoice.onchange_partner_id()
        invoice_line = invoice_line_proxy.create({
            'name': 'product_21_test',
            'product_id': product_21_consu.id,
            'price_unit': 0,
            'account_id': product_21_consu.categ_id.property_account_income_categ_id.id,
            'invoice_id': invoice.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 1000
        invoice._onchange_invoice_line_ids()
        invoice.action_invoice_open()

        return invoice

    def setUp(self):
        super(TestPaymentImputationWizard, self).setUp()

        self.iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        self.env.user.company_id.partner_id.property_account_position_id = self.iva_ri

        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'supplier': True,
            'customer': True,
            'property_account_position_id': self.iva_ri.id,

        })
        self.payment_imputation_wizard = self.env['payment.imputation.wizard'].create({
            'partner_id': self.partner.id,
            'payment_type': 'outbound'
        })

    def test_onchange_type(self):
        domain = self.payment_imputation_wizard.onchange_type()
        assert domain == {'domain': {'partner_id': [('supplier', '=', True)]}}

    def test_onchange_partner(self):
        invoice = self._create_invoice()
        self.payment_imputation_wizard.onchange_partner_id()
        assert len(self.payment_imputation_wizard.payment_imputation_line_ids) == 1
        invoice.type = 'out_invoice'
        self.payment_imputation_wizard.onchange_partner_id()
        assert not self.payment_imputation_wizard.payment_imputation_line_ids

    def test_onchange_journal(self):
        usd = self.env.ref('base.USD')
        assert self.payment_imputation_wizard.currency_id == self.env.user.company_id.currency_id
        self.payment_imputation_wizard.journal_id.currency_id = usd
        self.payment_imputation_wizard.onchange_journal_id()
        assert self.payment_imputation_wizard.currency_id == usd

    def test_invalid_amount(self):
        self.payment_imputation_wizard.advance_amount = -5
        with self.assertRaises(ValidationError):
            self.payment_imputation_wizard.create_payment()

    def test_not_amount(self):
        with self.assertRaises(ValidationError):
            self.payment_imputation_wizard.create_payment()

    def test_higher_amount_in_imputation_than_residual(self):
        self._create_invoice()
        self.payment_imputation_wizard.onchange_partner_id()
        self.payment_imputation_wizard.payment_imputation_line_ids.write({
            'amount': 10000
        })
        with self.assertRaises(ValidationError):
            self.payment_imputation_wizard.create_payment()

    def test_create_payment(self):
        self._create_invoice()
        self.payment_imputation_wizard.onchange_partner_id()
        self.payment_imputation_wizard.payment_imputation_line_ids.write({
            'amount': 500
        })
        self.payment_imputation_wizard.advance_amount = 50
        res = self.payment_imputation_wizard.create_payment()
        payment = self.env['account.payment'].browse(res.get('res_id'))
        assert payment.payment_imputation_ids == self.payment_imputation_wizard.payment_imputation_line_ids
        assert payment.partner_type == 'supplier'
        assert payment.payment_type == 'outbound'
        assert payment.partner_id == self.partner
        assert payment.amount == 550
        assert payment.advance_amount == 50

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
