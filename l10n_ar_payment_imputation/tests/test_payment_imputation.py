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

from odoo.addons.l10n_ar_account_payment.tests import set_up
from openerp.exceptions import ValidationError


class TestPaymentImputation(set_up.SetUp):

    def _create_invoice(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        product_21_consu = self.env['product.product'].create({
            'name': '21 consu',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.env.ref('l10n_ar.1_vat_21_ventas').id])]
        })
        invoice = invoice_proxy.create({
            'partner_id': self.partner.id,
            'type': 'out_invoice'
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

    def _create_imputation(self, invoice, payment):
        return self.env['payment.imputation.line'].create({
            'invoice_id': invoice.id,
            'payment_id': payment.id
        })

    def setUp(self):
        super(TestPaymentImputation, self).setUp()
        self.imputation = self.env['payment.imputation.line'].create({
            'invoice_id': self.invoice.id,
            'payment_id': self.customer_payment.id,
        })

    def test_payment_imputation_no_move(self):
        self.invoice.journal_id.update_posted = True
        self.invoice.move_id.button_cancel()
        self.invoice.move_id = None
        self.invoice.move_id.unlink()
        self.imputation.amount = 500
        self.customer_payment.pos_ar_id = self.pos_inbound
        with self.assertRaises(ValidationError):
            self.customer_payment.post_l10n_ar()

    def test_imputation_no_invoice(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.imputation.unlink()
        self.customer_payment.post_l10n_ar()

    def test_create_imputations_from_partner(self):
        self.imputation.unlink()
        self._create_invoice()
        self.customer_payment.onchange_partner_imputation()
        assert len(self.customer_payment.payment_imputation_ids) == 2

    """ Tests de 1 sola factura """
    def test_total_payment_partial_invoice(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.imputation.amount = 500
        self.customer_payment.post_l10n_ar()

        assert self.invoice.residual == 710

    def test_partial_payment_partial_invoice(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.imputation.amount = 300
        self.customer_payment.post_l10n_ar()

        assert self.invoice.residual == 910

    def test_total_payment_total_invoice(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = self.invoice.residual_signed
        self.customer_payment.amount = self.invoice.residual_signed
        self.imputation.amount = self.imputation.invoice_id.residual_signed
        self.customer_payment.post_l10n_ar()

        assert self.invoice.state == 'paid'

    def test_higher_imputation_than_payment_amount(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.imputation.amount = 500.01

        with self.assertRaises(ValidationError):
            self.customer_payment.post_l10n_ar()

    def test_higher_imputation_than_invoice_amount(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = 1500
        self.customer_payment.amount = 1500
        self.imputation.amount = 1500

        with self.assertRaises(ValidationError):
            self.customer_payment.post_l10n_ar()

    """ Tests de multiples facturas """
    def test_total_imputation_multiple_invoices(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = 2420
        self.customer_payment.amount = 2420

        self.imputation.amount = 1210
        invoice = self._create_invoice()
        imputation = self._create_imputation(invoice, self.customer_payment)
        imputation.amount = 1210

        self.customer_payment.post_l10n_ar()
        assert self.invoice.state == 'paid'
        assert invoice.state == 'paid'

    def test_total_imputation_one_invoice_partial_another(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = 2000
        self.customer_payment.amount = 2000

        self.imputation.amount = 1210
        invoice = self._create_invoice()
        imputation = self._create_imputation(invoice, self.customer_payment)
        imputation.amount = 790

        self.customer_payment.post_l10n_ar()
        assert self.invoice.state == 'paid'
        assert invoice.residual == 420

    def test_partial_imputation_two_invoices(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = 2000
        self.customer_payment.amount = 2000

        self.imputation.amount = 1000
        invoice = self._create_invoice()
        imputation = self._create_imputation(invoice, self.customer_payment)
        imputation.amount = 1000

        self.customer_payment.post_l10n_ar()

        assert self.invoice.residual == 210
        assert invoice.residual == 210

    def test_higher_payment_amount_than_invoices(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.payment_line.amount = 3000
        self.customer_payment.amount = 3000

        self.imputation.amount = 1000
        invoice = self._create_invoice()
        imputation = self._create_imputation(invoice, self.customer_payment)
        imputation.amount = 1000

        self.customer_payment.post_l10n_ar()
        move_line = self.env['account.move.line'].search([('payment_id', '=', self.customer_payment.id)]). \
            filtered(lambda x: x.account_id.user_type_id.type == 'receivable')
        assert self.invoice.residual == 210
        assert invoice.residual == 210
        assert abs(move_line.amount_residual) == 1000
        assert self.customer_payment.payment_imputation_difference == 1000

    """ Multicurrency """
    def test_multilcurrency_imputation(self):
        usd = self.env.ref('base.USD')
        self.env['res.currency.rate'].create({
            'currency_id': usd.id,
            'rate': 0.1
        })
        self.customer_payment.write({
            'pos_ar_id': self.pos_inbound.id,
            'amount': 100,
            'currency_id': usd.id
        })
        self.payment_line.amount = 100
        self.imputation.amount = 100
        self.customer_payment.post_l10n_ar()

        assert self.invoice.residual == 210


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
