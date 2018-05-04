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

from datetime import timedelta

from openerp.exceptions import ValidationError
from openerp.fields import date
from openerp.tests.common import TransactionCase


class TestWizardGeneralLedgerExcel(TransactionCase):

    def create_partner(self):
        self.partner = self.env['res.partner'].create({
            'name': "Partner",
        })

    def create_account_type(self):
        self.account_type = self.env['account.account.type'].create({
            'name': "Ejemplo",
        })

    def create_accounts(self):
        self.account_one = self._create_account(123456, "Cuenta uno")
        self.account_two = self._create_account(654321, "Cuenta dos")
        self.account_three = self._create_account(456789, "Cuenta tres")

    def create_journal(self):
        self.journal = self.env['account.journal'].create({
            'code': "DIA",
            'name': "Diario",
            'user_type_id': self.account_type.id,
            'type': 'sale',
        })

    def create_move(self):
        self.move = self.env['account.move'].create({
            'name': 'Asiento ejemplo nombre',
            'date': date.today(),
            'ref': 'Asiento ejemplo',
            'journal_id': self.journal.id,
        })

    def create_move_lines(self):
        self._create_move_line(1000, 0, "Linea ejemplo 1", self.account_one)
        self._create_move_line(0, 700, "Linea ejemplo 2", self.account_two)
        self._create_move_line(0, 300, "Linea ejemplo 3", self.account_three)

    def create_wizard(self):
        self.wizard = self.env['wizard.general.ledger.excel'].create({
            'date_from': date.today() - timedelta(days=1),
            'date_to': date.today(),
        })

    def _create_account(self, code, name):
        return self.env['account.account'].create({
            'code': code,
            'name': name,
            'user_type_id': self.account_type.id,
        })

    def _create_move_line(self, debit, credit, name, account):
        self.env['account.move.line'].with_context(check_move_validity=False).create({
            'move_id': self.move.id,
            'debit': debit,
            'credit': credit,
            'name': name,
            'account_id': account.id,
            'partner_id': self.partner.id,
        })

    def setUp(self):
        super(TestWizardGeneralLedgerExcel, self).setUp()
        self.create_partner()
        self.create_account_type()
        self.create_accounts()
        self.create_journal()
        self.create_move()
        self.create_move_lines()
        self.create_wizard()

    def test_check_dates(self):
        with self.assertRaises(ValidationError):
            self.wizard.date_from = date.today() + timedelta(days=1)

    def test_values(self):
        values = self.wizard.get_values(self.move)
        assert values.keys() == ["Asiento ejemplo nombre"]
        list = values[self.move.name]
        print values
        today = date.today().strftime('%d/%m/%Y')
        assert list[2] == (today, "123456", "Cuenta uno", 1000, '-', "Linea ejemplo 1", "Partner")
        assert list[1] == (today, "654321", "Cuenta dos", '-', 700, "Linea ejemplo 2", "Partner")
        assert list[0] == (today, "456789", "Cuenta tres", '-', 300, "Linea ejemplo 3", "Partner")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
