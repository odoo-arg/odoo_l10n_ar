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


class TestAccountOwnCheck(common.TransactionCase):

    def setUp(self):
        super(TestAccountOwnCheck, self).setUp()
        own_check_proxy = self.env['account.own.check']
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        journal.write({
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'bank_acc_number': 'Banco 1231'
        })
        checkbook = self.env['account.checkbook'].create({
            'name': 'Chequera',
            'payment_type': 'postdated',
            'journal_id': journal.id,
            'number_from': '1',
            'number_to': '10',
        })
        self.own_check_draft = own_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': checkbook.id,
            'state': 'draft'
        })
        self.own_check_handed = own_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': checkbook.id,
            'state': 'handed'
        })
        self.own_checks = self.own_check_draft | self.own_check_handed

    def test_cancel_check(self):
        self.own_check_handed.state = 'draft'
        self.own_checks.cancel_check()
        assert all(check == 'canceled' for check in self.own_checks.mapped("state"))

    def test_invalid_cancel_check(self):
        with pytest.raises(ValidationError):
            self.own_checks.cancel_check()

    def test_revert_canceled_check(self):
        self.own_checks.write({'state': 'canceled'})
        self.own_checks.revert_canceled_check()
        assert all(check == 'draft' for check in self.own_checks.mapped("state"))

    def test_invalid_revert_canceled_check(self):
        with pytest.raises(ValidationError):
            self.own_checks.revert_canceled_check()

    def test_reject_check(self):
        self.own_check_draft.state = 'handed'
        self.own_checks.reject_check()
        assert all(check == 'rejected' for check in self.own_checks.mapped("state"))

    def test_invalid_reject_check(self):
        with pytest.raises(ValidationError):
            self.own_checks.reject_check()

    def test_revert_reject(self):
        self.own_checks.write({'state': 'rejected'})
        self.own_checks.revert_reject()
        assert all(check == 'handed' for check in self.own_checks.mapped("state"))

    def test_invalid_revert_reject(self):
        with pytest.raises(ValidationError):
            self.own_checks.revert_reject()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
