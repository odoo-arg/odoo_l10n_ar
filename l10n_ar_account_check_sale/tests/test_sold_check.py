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

from datetime import timedelta, datetime
from odoo.tests import common
from openerp import fields
from openerp.exceptions import ValidationError, MissingError


class TestSoldCheck(common.TransactionCase):

    def setUp(self):
        super(TestSoldCheck, self).setUp()
        third_check_proxy = self.env['account.third.check']
        date_today = fields.Date.context_today(third_check_proxy)
        self.third_check = third_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'amount': 1750,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today,
            'state': 'wallet'
        })
        self.third_check_2 = third_check_proxy.create({
            'name': '412414',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'postdated',
            'amount': 750,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today,
            'state': 'wallet'
        })
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        journal.update_posted = True
        self.sold_check = self.env['account.sold.check'].create({
            'journal_id': journal.id,
            'bank_account_id': journal.id,
            'date': fields.Date.context_today(self.env['account.sold.check']),
            'account_third_check_ids': [(6, 0, [self.third_check.id, self.third_check_2.id])],
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id
        })

    def test_negative_amounts(self):
        with self.assertRaises(ValidationError):
            self.sold_check.commission = -10

    def test_create_sequence(self):
        sequence = self.env['ir.sequence'].next_by_code('account.sold.check.sequence')
        sold_check = self.env['account.sold.check'].create({
            'journal_id': self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos').id,
            'date': fields.Date.context_today(self.env['account.sold.check'])
        })
        assert sold_check.name == sequence[:-1]+str(int(sequence[-1:])+1)

    def test_post_sold_check(self):
        self.sold_check.post()
        assert self.sold_check.move_id
        assert self.sold_check.state == 'sold'
        assert all(check.state == 'sold' for check in self.sold_check.account_third_check_ids)

    def test_check_no_partner_or_bank(self):
        self.sold_check.bank_account_id = None
        with self.assertRaises(ValidationError):
            self.sold_check.post()

    def test_post_no_checks(self):
        self.sold_check.account_third_check_ids = None
        with self.assertRaises(ValidationError):
            self.sold_check.post()

    def test_cancel_and_draft(self):
        self.sold_check.cancel()
        assert self.sold_check.state == 'canceled'
        self.sold_check.draft()
        assert self.sold_check.state == 'draft'

    def test_cancel_sold_check_with_move(self):
        self.sold_check.post()
        move = self.sold_check.move_id
        self.sold_check.cancel()
        # Los cheques deberian estar en cartera despues de anularse la venta
        assert all(check.state == 'wallet' for check in self.sold_check.account_third_check_ids)

        assert not self.sold_check.move_id
        # Deberia haberse borrado el asiento
        with self.assertRaises(MissingError):
            move.post()

    def test_check_currencies(self):
        self.third_check.currency_id = self.env.ref('base.USD').id
        with self.assertRaises(ValidationError):
            self.sold_check.account_third_check_ids = [(6, 0, [self.third_check.id, self.third_check_2.id])]

    def test_move(self):

        new_date = datetime.strptime(self.sold_check.date, '%Y-%m-%d') + timedelta(days=10)
        self.sold_check.write({
            'date': new_date
        })
        move = self.sold_check._create_move(self.sold_check.name)
        assert move.journal_id == self.sold_check.journal_id
        assert move.date == new_date.strftime('%Y-%m-%d')

    def test_move_line_vals(self):
        self.sold_check.post()
        lines = self.sold_check.move_id.line_ids
        assert len(lines) == 2
        debit_line = lines.filtered(lambda x: x.debit > 0)
        credit_line = lines.filtered(lambda x: x.credit > 0)
        # Deberia tomar la cuenta del diario / cuenta bancaria donde se vende
        assert debit_line.account_id == self.sold_check.account_id
        # Para el caso del credito restar la cuenta de cheques configurada en la empresa
        assert credit_line.account_id == self.env.user.company_id.third_check_account_id
        assert not (lines.mapped('currency_id') and lines.mapped('amount_currency'))
        # Chequeamos los valores
        assert debit_line.debit == self.third_check.amount+self.third_check_2.amount
        assert not debit_line.credit
        assert credit_line.credit == self.third_check.amount + self.third_check_2.amount
        assert not credit_line.debit

    def test_move_line_vals_with_commission(self):
        self.sold_check.commission = 10
        self.sold_check.interests = 5
        self.sold_check.commission_account_id = self.env.ref('l10n_ar.1_caja_pesos').id
        self.sold_check.interest_account_id = self.env.ref('l10n_ar.1_banco').id
        self.sold_check.post()
        lines = self.sold_check.move_id.line_ids
        assert len(lines) == 4
        debit_lines = lines.filtered(lambda x: x.debit > 0)
        credit_line = lines.filtered(lambda x: x.credit > 0)
        # Deberia tomar la cuenta del diario / cuenta bancaria donde se vende
        assert credit_line.account_id == self.env.user.company_id.third_check_account_id
        # Para el caso del credito restar la cuenta de cheques configurada en la empresa
        assert any(line.account_id == self.sold_check.account_id for line in debit_lines)
        # Validamos que esten las cuentas configuradas en comision e intereses
        assert any(line.account_id == self.sold_check.commission_account_id for line in debit_lines)
        assert any(line.account_id == self.sold_check.interest_account_id for line in debit_lines)

    def test_move_lines_not_account_journal(self):
        self.sold_check.account_id = None
        with self.assertRaises(ValidationError):
            self.sold_check.post()

    def test_move_lines_not_account_third_check(self):
        self.env.user.company_id.third_check_account_id = None
        with self.assertRaises(ValidationError):
            self.sold_check.post()

    def test_move_lines_multi_currency(self):
        usd = self.env.ref('base.USD')
        self.env['res.currency.rate'].create({
            'rate': 0.1,
            'currency_id': usd.id,
            'name': self.sold_check.date
        })
        self.third_check.currency_id = usd.id
        self.third_check_2.currency_id = usd.id
        self.sold_check.account_third_check_ids = [(6, 0, [self.third_check.id, self.third_check_2.id])]
        self.sold_check.post()
        lines = self.sold_check.move_id.line_ids
        debit_line = lines.filtered(lambda x: x.debit > 0)
        credit_line = lines.filtered(lambda x: x.credit > 0)
        amount = (self.third_check.amount+self.third_check_2.amount)/round(usd.rate, 2)
        assert debit_line.debit == amount
        assert credit_line.credit == amount
        assert debit_line.amount_currency == self.third_check.amount+self.third_check_2.amount
        assert credit_line.amount_currency == -(self.third_check.amount+self.third_check_2.amount)
        assert lines.mapped('currency_id') == usd

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
