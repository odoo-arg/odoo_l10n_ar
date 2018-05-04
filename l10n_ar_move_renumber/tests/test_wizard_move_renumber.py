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
from datetime import timedelta

from openerp.exceptions import ValidationError
from openerp.fields import date
from openerp.tests.common import TransactionCase


class TestWizardMoveRenumber(TransactionCase):

    def create_journal(self):
        account_type = self.env['account.account.type'].create({
            'name': "Ejemplo",
        })
        self.journal = self.env['account.journal'].create({
            'code': "DIA",
            'name': "Diario",
            'user_type_id': account_type.id,
            'type': 'sale',
        })

    def create_moves(self):
        self.move_one = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'date': date.today() - timedelta(days=1),
            'name': "DIA/{}/0003".format(date.today().year),
        })
        self.move_two = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'date': date.today(),
            'name': "DIA/{}/0002".format(date.today().year),
        })
        self.move_three = self.env['account.move'].create({
            'journal_id': self.journal.id,
            'date': date.today(),
            'name': "DIA/{}/0001".format(date.today().year),
        })

    def create_wizard(self):
        self.wizard = self.env['wizard.move.renumber'].create({
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today(),
            'prefix': "WIZARD/",
            'minimum_digits': 3,
        })

    def setUp(self):
        super(TestWizardMoveRenumber, self).setUp()
        self.create_journal()
        self.create_moves()
        self.create_wizard()

    def test_check_dates(self):
        with self.assertRaises(ValidationError):
            self.wizard.date_from = date.today() + timedelta(days=1)

    def test_check_initial_number(self):
        with self.assertRaises(ValidationError):
            self.wizard.initial_number = 0

    def test_check_mininum_digits(self):
        with self.assertRaises(ValidationError):
            self.wizard.minimum_digits = 0

    def test_renumber(self):
        self.wizard.renumber()
        assert self.move_one.name == "WIZARD/001"
        assert self.move_two.name == "WIZARD/002"
        assert self.move_three.name == "WIZARD/003"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
