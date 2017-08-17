# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.addons.l10n_ar_account_payment.tests import set_up
from openerp.exceptions import ValidationError


class TestAccountPayment(set_up.SetUp):

    def test_check_state_draft(self):
        report = self.env['report.l10n_ar_account_payment_report.report_account_payment'].new({})
        with self.assertRaises(ValidationError):
            report.render_html(self.customer_payment.id)

    def test_check_state_posted(self):
        self.customer_payment.state = 'posted'
        report = self.env['report.l10n_ar_account_payment_report.report_account_payment'].new({})
        report.render_html(self.customer_payment.id)

    def test_print_internal_payment(self):
        self.customer_payment.write({
            'state': 'posted',
            'payment_type': 'transfer'
        })
        report = self.env['report.l10n_ar_account_payment_report.report_account_payment'].new({})
        with self.assertRaises(ValidationError):
            report.render_html(self.customer_payment.id)

    def test_partial_ids_customer(self):
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 1210
        })
        self.payment_line.amount = 1210
        self.customer_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.customer_payment._get_partial_ids()
        assert partial_id.amount == 1210
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').residual == 0
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_different_residual_customer(self):
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 1000
        })
        self.payment_line.amount = 1000
        self.customer_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.customer_payment._get_partial_ids()
        assert partial_id.amount == 1000
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').residual == 210
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_supplier(self):
        self.invoice.journal_id.update_posted = True
        self.invoice.action_invoice_cancel()
        self.invoice.write({
            'state': 'draft',
            'type': 'in_invoice',
        })
        self.invoice.action_invoice_open()
        self.supplier_payment.write({
            'pos_ar_id': self.supplier_payment.get_pos(self.supplier_payment.payment_type),
            'payment_id': self.supplier_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 1210
        })
        self.payment_line.write({
            'amount': 1210,
            'payment_id': self.supplier_payment.id
        })
        self.supplier_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.supplier_payment._get_partial_ids()
        assert partial_id.amount == 1210
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').residual == 0
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_different_residual_supplier(self):
        self.invoice.journal_id.update_posted = True
        self.invoice.action_invoice_cancel()
        self.invoice.write({
            'state': 'draft',
            'type': 'in_invoice',
        })
        self.invoice.action_invoice_open()
        self.supplier_payment.write({
            'pos_ar_id': self.supplier_payment.get_pos(self.supplier_payment.payment_type),
            'payment_id': self.supplier_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 500
        })
        self.payment_line.write({
            'amount': 500,
            'payment_id': self.supplier_payment.id
        })
        self.supplier_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.supplier_payment._get_partial_ids()
        assert partial_id.amount == 500
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').residual == 710
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_currency(self):
        self.invoice.journal_id.update_posted = True
        self.invoice.action_invoice_cancel()
        self.invoice.state = 'draft'
        usd = self.env.ref('base.USD')
        self.env['res.currency.rate'].create({
            'rate': 0.1,
            'currency_id': usd.id,
            'name': self.invoice.date
        })
        self.invoice.currency_id = usd.id
        self.invoice.action_invoice_open()
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 1210
        })
        self.payment_line.amount = 1210
        self.customer_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.customer_payment._get_partial_ids()
        assert partial_id.amount_currency == 121
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').residual == 1089
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_usd(self):
        usd = self.env.ref('base.USD')
        self.env['res.currency.rate'].create({
            'rate': 0.1,
            'currency_id': usd.id,
            'name': self.invoice.date
        })
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'currency_id': usd.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 100
        })
        self.payment_line.currency_id = usd.id
        self.payment_line.amount = 100
        self.customer_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.customer_payment._get_partial_ids()
        assert not partial_id.amount_currency
        assert partial_id.amount == 1000
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').residual == 210
        assert partial_id.mapped('debit_move_id').mapped('invoice_id').amount_total == 1210

    def test_partial_ids_usd_payment_usd(self):
        self.invoice.journal_id.update_posted = True
        self.invoice.action_invoice_cancel()
        self.invoice.write({
            'state': 'draft',
            'type': 'in_invoice'
        })
        usd = self.env.ref('base.USD')
        self.env['res.currency.rate'].create({
            'rate': 0.1,
            'currency_id': usd.id,
            'name': self.invoice.date
        })
        self.invoice.currency_id = usd.id
        self.invoice.action_invoice_open()
        self.supplier_payment.write({
            'pos_ar_id': self.supplier_payment.get_pos(self.supplier_payment.payment_type),
            'payment_id': self.supplier_payment.id,
            'currency_id': usd.id,
            'invoice_ids': [(6, 0, [self.invoice.id])],
            'amount': 850
        })
        self.payment_line.write({
            'currency_id': usd.id,
            'amount': 850,
            'payment_id': self.supplier_payment.id,
        })
        self.supplier_payment.post_l10n_ar()

        # Chequeamos los documentos imputados
        partial_id = self.supplier_payment._get_partial_ids()
        assert partial_id.amount_currency == 850
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').residual == 360
        assert partial_id.mapped('credit_move_id').mapped('invoice_id').amount_total == 1210

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
