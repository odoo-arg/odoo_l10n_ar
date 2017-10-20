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

from dateutil.relativedelta import relativedelta
from openerp.tests.common import TransactionCase
from random import randint
from datetime import datetime
from openerp.exceptions import except_orm


class TestBankReconcile(TransactionCase):

    def create_account(self):
        random = str(randint(1000, 2000)) + 'A'
        self.account = self.env['account.account'].create({
            'code': random,
            'name': 'TEST ACCOUNT',
            'type': 'liquidity',
            'user_type': self.env.ref('l10n_ar_chart_of_account.account_type_asset').id
        })

    def create_fiscalyear(self):
        self.fiscal_year = self.env['account.fiscalyear'].create({
            'name': '01/2017',
            'code': '01/2017',
            'date_start': (datetime.today() + relativedelta(months=11)).strftime('%Y-%m-%d'),
            'date_stop': (datetime.today() + relativedelta(months=13)).strftime('%Y-%m-%d'),
        })
        self.fiscal_year.create_period()
        self.periods = self.fiscal_year.period_ids

    def create_reconcile_USD(self):
        self.reconcile_USD = self.env['account.bank.reconcile'].create({
            'account_id': self.account.id,
            'name': 'CONCILIACION BANCARIA EXTRANJERA'
        })

    def create_journal(self):
        self.journal = self.env['account.journal'].create({
            'name': 'CYP',
            'code': 'CYP',
            'type': 'bank',
        })

    def setUp(self):
        super(TestBankReconcile, self).setUp()
        self.create_account()
        self.create_fiscalyear()
        self.create_reconcile_USD()
        self.create_journal()
        # Creo un nuevo asiento para la moneda extranjera
        self.move_currency = self.env['account.move'].create({
            'name': 'Test moneda extranjera',
            'journal_id': self.journal.id,
            'ref': 'Referencia asiento contable',
            'date': datetime.today()
        })
        # Creo las lineas para el asiento con la moneda correspondiente
        self.move_line_currency_1 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'debito 1',
            'account_id': self.account.id,
            'debit': 1000,
            'date': datetime.today(),
            'currency_id': self.env.ref('base.USD').id,
            'amount_currency': 100,
            'move_id': self.move_currency.id,
            'journal_id': self.journal.id,
            'period_id': self.periods[0].id,
        })
        self.move_line_currency_5 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'credito 2',
            'account_id': self.account.id,
            'credit': 1000,
            'date': datetime.today(),
            'currency_id': self.env.ref('base.USD').id,
            'amount_currency': -100,
            'move_id': self.move_currency.id,
            'journal_id': self.journal.id,
            'period_id': self.periods[0].id,
        })
        self.move_line_currency_2 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'debito 2',
            'account_id': self.account.id,
            'debit': 2000,
            'date': datetime.today(),
            'currency_id': self.env.ref('base.USD').id,
            'amount_currency': 200,
            'move_id': self.move_currency.id,
            'journal_id': self.journal.id,
            'period_id': self.periods[0].id,
        })
        self.move_line_currency_4 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'credito 1',
            'account_id': self.account.id,
            'credit': 2000,
            'date': datetime.today(),
            'currency_id': self.env.ref('base.USD').id,
            'amount_currency': -200,
            'move_id': self.move_currency.id,
            'journal_id': self.journal.id,
            'period_id': self.periods[0].id,
        })

    def test_reconcile_move_with_other_currency(self):
        """ 
        Itento crear una conciliacion con monedas distintas de  
        """
        # Creo move line sin moneda
        new_move_line_currency_1 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'credito new',
            'account_id': self.account.id,
            'credit': 1000,
            'date': datetime.today(),
            'move_id': self.move_currency.id
        })
        self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'debito new',
            'account_id': self.account.id,
            'debit': 1000,
            'date': datetime.today(),
            'move_id': self.move_currency.id
        })
        new_move_line_currency_1.account_id.write({'currency_id': self.env.ref('base.USD').id})
        move_lines = new_move_line_currency_1
        active_ids = move_lines.ids
        wizard = self.env['bank.reconciliation.wizard'].with_context(active_ids=active_ids).create({
            'period_id': self.periods[1].id,
        })
        with self.assertRaises(except_orm):
            wizard.create_conciliation()

    def test_reconcile_with_USD(self):
        """
        Concilio movimientos en dolares en una conciliacion con cuenta en dolares
        """
        move_lines = self.move_line_currency_1 | self.move_line_currency_2
        self.move_line_currency_1.account_id.write({'currency_id': self.env.ref('base.USD').id})
        active_ids = move_lines.ids
        wizard = self.env['bank.reconciliation.wizard'].with_context(active_ids=active_ids).create({
            'period_id': self.periods[1].id,
        })
        wizard.create_conciliation()

    def test_reconcile_with_USD_and_check_balance(self):
        """
        Concilio cuenta en dolares y verifico el balance en pesos y en USD
        """
        move_lines = self.move_line_currency_1 | self.move_line_currency_2
        self.move_line_currency_1.account_id.write({'currency_id': self.env.ref('base.USD').id})
        active_ids = move_lines.ids
        wizard = self.env['bank.reconciliation.wizard'].with_context(active_ids=active_ids).create({
            'period_id': self.periods[1].id,
        })
        wizard.create_conciliation()
        assert self.reconcile_USD.bank_reconcile_line_ids[0].current_balance == 3000
        assert self.reconcile_USD.bank_reconcile_line_ids[0].last_balance == 0
        assert self.reconcile_USD.bank_reconcile_line_ids[0].current_balance_currency == 300
        assert self.reconcile_USD.bank_reconcile_line_ids[0].last_balance_currency == 0

        move_lines = self.move_line_currency_5
        self.move_line_currency_1.account_id.write({'currency_id': self.env.ref('base.USD').id})
        active_ids = move_lines.ids
        wizard = self.env['bank.reconciliation.wizard'].with_context(active_ids=active_ids).create({
            'period_id': self.periods[2].id,
        })
        wizard.create_conciliation()
        assert self.reconcile_USD.bank_reconcile_line_ids[0].current_balance == 2000
        assert self.reconcile_USD.bank_reconcile_line_ids[0].last_balance == 3000
        assert self.reconcile_USD.bank_reconcile_line_ids[0].current_balance_currency == 200
        assert self.reconcile_USD.bank_reconcile_line_ids[0].last_balance_currency == 300

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
