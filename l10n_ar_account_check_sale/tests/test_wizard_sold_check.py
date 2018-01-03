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
from openerp import fields
from openerp.exceptions import ValidationError
from test_sold_check import TestSoldCheck


class TestWizardSellCheck(TestSoldCheck):

    def setUp(self):
        super(TestWizardSellCheck, self).setUp()
        slip_proxy = self.env['wizard.sell.check']
        date_today = fields.Date.context_today(slip_proxy)
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        journal.update_posted = True
        check_ids = [self.third_check.id, self.third_check_2.id]
        self.wizard_sold_check = slip_proxy.with_context(active_ids=check_ids).create({
            'journal_id': journal.id,
            'date': date_today,
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'commission_account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'interest_account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'commission': 10,
            'interests': 5
        })

    def test_create_sold_check(self):
        self.sold_check.account_third_check_ids = None
        res = self.wizard_sold_check.create_sold_check_document()
        sold_check = self.env['account.sold.check'].browse(res.get('res_id'))
        assert sold_check.date == self.wizard_sold_check.date
        assert sold_check.journal_id == self.wizard_sold_check.journal_id
        assert sold_check.amount == self.wizard_sold_check.amount
        assert sold_check.account_third_check_ids == self.third_check | self.third_check_2
        assert sold_check.state == 'draft'
        assert sold_check.commission_account_id == self.wizard_sold_check.commission_account_id
        assert sold_check.interest_account_id == self.wizard_sold_check.interest_account_id
        assert sold_check.commission == self.wizard_sold_check.commission
        assert sold_check.interests == self.wizard_sold_check.interests

    def test_non_wallet_check(self):
        self.sold_check.account_third_check_ids.write({'state': 'handed'})
        with self.assertRaises(ValidationError):
            self.wizard_sold_check.create_sold_check_document()

    def test_negative_amounts(self):
        with self.assertRaises(ValidationError):
            self.wizard_sold_check.commission = -10

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
