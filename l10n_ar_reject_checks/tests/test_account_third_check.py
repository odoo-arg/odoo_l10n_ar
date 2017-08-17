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

import pytest
from odoo.tests import common
from openerp import fields
from openerp.exceptions import ValidationError


class TestAccountThirdCheck(common.TransactionCase):

    def setUp(self):
        super(TestAccountThirdCheck, self).setUp()
        third_check_proxy = self.env['account.third.check']
        date_today = fields.Date.context_today(third_check_proxy)
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        payment = self.env['account.payment'].create({
            'state': 'posted',
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'amount': 23
        })
        deposit_slip = self.env['account.deposit.slip'].create({
            'journal_id': journal.id,
            'date': fields.Date.context_today(self.env['account.deposit.slip']),
        })
        self.third_check_wallet = self.env['account.third.check'].create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'amount': 1300,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today,
            'state': 'wallet'
        })
        self.third_check_handed = self.env['account.third.check'].create({
            'name': '5125125',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'postdated',
            'amount': 252,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today,
            'state': 'handed',
            'account_payment_ids': [(6, 0, [payment.id])]
        })
        self.third_check_deposited = self.env['account.third.check'].create({
            'name': '5125125',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'postdated',
            'amount': 252,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today,
            'state': 'wallet',
            'deposit_slip_ids': [(6, 0, [deposit_slip.id])]
        })
        self.third_check_deposited.post_deposit_slip()
        self.third_checks = self.third_check_wallet | self.third_check_handed | self.third_check_deposited

    def test_reject_check(self):
        self.third_checks.reject_check()
        assert all(check == 'rejected' for check in self.third_checks.mapped("state"))

    def test_button_reject_check(self):
        self.third_checks.button_reject_check()
        assert all(check == 'rejected' for check in self.third_checks.mapped("state"))

    def test_invalid_reject_check(self):
        self.third_check_handed.state = 'draft'
        with pytest.raises(ValidationError):
            self.third_checks.reject_check()

    def test_revert_check(self):
        """ Cada cheque deberia tener su estado original """
        self.third_checks.reject_check()
        self.third_checks.revert_reject()
        assert self.third_check_wallet.state == 'wallet'
        assert self.third_check_handed.state == 'handed'
        assert self.third_check_deposited.state == 'deposited'

    def test_button_revert_check(self):
        self.third_checks.reject_check()
        self.third_checks.button_revert_reject()
        assert self.third_check_wallet.state == 'wallet'
        assert self.third_check_handed.state == 'handed'
        assert self.third_check_deposited.state == 'deposited'

    def test_invalid_revert_check(self):
        with pytest.raises(ValidationError):
            self.third_checks.revert_reject()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
