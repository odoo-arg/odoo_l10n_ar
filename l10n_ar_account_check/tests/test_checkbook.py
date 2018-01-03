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

import set_up
from openerp.exceptions import ValidationError


class TestCheckbook(set_up.SetUp):

    def setUp(self):
        super(TestCheckbook, self).setUp()
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        journal.write({
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'bank_acc_number': 'Banco 1231'
        })
        self.checkbook = self.env['account.checkbook'].create({
            'name': 'Chequera',
            'payment_type': 'postdated',
            'journal_id': journal.id,
            'number_from': '1',
            'number_to': '10',
            'account_id': self.env['account.account'].search([], limit=1).id,
        })

    def test_numbers_digits(self):
        with self.assertRaises(ValidationError):
            self.checkbook.number_from = 'A123'
        with self.assertRaises(ValidationError):
            self.checkbook.number_to = 'AAXX'
        self.checkbook.write({
            'number_to': 100,
            'number_from': 50
        })

    def test_numbers_range(self):
        with self.assertRaises(ValidationError):
            self.checkbook.number_from = 0

        with self.assertRaises(ValidationError):
            self.checkbook.number_to = -50

        with self.assertRaises(ValidationError):
            self.checkbook.write({
                'number_from': 50,
                'number_to': 10
            })

        with self.assertRaises(ValidationError):
            self.checkbook.write({
                'number_from': 10,
                'number_to': 1000
            })

    def test_generate_checks(self):
        # Probamos crear los cheques de una chequera
        self.checkbook.generate_checks()
        checks = self.env['account.own.check'].search([])
        assert len(checks) == 10
        assert checks.mapped('checkbook_id') == self.checkbook
        name_list = [unicode(str(value), 'utf-8') for value in
                     range(int(self.checkbook.number_from), int(self.checkbook.number_to)+1)]
        for check_name in checks.mapped('name'):
            assert check_name in name_list
        assert checks.mapped('bank_id') == self.checkbook.journal_id.bank_id
        assert checks.mapped('payment_type')[0] == self.checkbook.payment_type

    def test_validate_checkbook_fields(self):
        self.checkbook._validate_checkbook_fields()
        self.checkbook.journal_id.bank_id = None
        with self.assertRaises(ValidationError):
            self.checkbook._validate_checkbook_fields()

    def test_generate_checks_when_checks_used(self):
        self.checkbook.generate_checks()
        self.checkbook.account_draft_own_check_ids[0].state = 'handed'
        with self.assertRaises(ValidationError):
            self.checkbook.generate_checks()

    def test_used_and_draft_checks_in_checkbook(self):
        self.checkbook.generate_checks()
        assert len(self.checkbook.account_draft_own_check_ids) == 10
        assert not len(self.checkbook.account_used_own_check_ids)
        search = self.checkbook._search_draft_checks('in', self.checkbook.account_draft_own_check_ids.ids)
        assert [('id', 'in', self.checkbook.account_draft_own_check_ids.ids)] == search
        self.checkbook.account_draft_own_check_ids[0].state = 'handed'
        assert len(self.checkbook.account_draft_own_check_ids) == 9
        assert len(self.checkbook.account_used_own_check_ids) == 1
        self.checkbook.account_draft_own_check_ids.write({'state': 'handed'})
        assert not len(self.checkbook.account_draft_own_check_ids)
        assert len(self.checkbook.account_used_own_check_ids) == 10

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
