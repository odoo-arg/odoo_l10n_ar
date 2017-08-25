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

from openerp.tests.common import TransactionCase
from psycopg2._psycopg import IntegrityError
from openerp.exceptions import ValidationError


class TestBankReconcile(TransactionCase):

    def setUp(self):
        super(TestBankReconcile, self).setUp()
        # Creo la conciliacion bancaria
        self.bank_reconcile = self.env['account.bank.reconcile'].create({
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'name': 'RECONCILE CAJA PESOS',
        })
        # Creo el diario para usar en el asiento
        self.journal = self.env['account.journal'].create({
            'name': 'CYP',
            'code': 'CYP',
            'type': 'bank',
        })
        # Creo el asiento con los datos necesarios
        self.move = self.env['account.move'].create({
            'name': 'Test',
            'journal_id': self.journal.id,
            'ref': 'Referencia asiento contable',
            'date': '2017-08-24',
        })
        # Creo las lineas de los asientos con el with context para que no valide el balanceo del asientos
        self.move_line_1 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Caja 1',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'debit': 10,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        self.move_line_2 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Caja 2',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'debit': 20,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        self.move_line_3 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Caja 3',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'debit': 30,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        self.move_line_4 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Caja 4',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'debit': 40,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        self.move_line_5 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Banco 1',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'credit': 100,
            'date': '2017-08-24',
            'move_id': self.move.id
        })

    def test_reconcile_move_line(self):
        """
        Intento crear una conciliacion con las lineas
        """
        move_lines = self.move_line_1 | self.move_line_2 | self.move_line_3 | self.move_line_4 | self.move_line_5
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()

    def test_reconcile_move_line_and_write(self):
        """
        Creo la conciliacion y luego intento editar la linea conciliada
        """
        move_lines = self.move_line_1 | self.move_line_2 | self.move_line_3 | self.move_line_4 | self.move_line_5
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        with self.assertRaises(ValidationError):
            for line in move_lines:
                line.write({'debit': 1000})

    def test_check_current_balance(self):
        """
        Creo una conciliacion con las lineas y chequeo si el balance del rango de fechas es correcto
        """
        move_lines = self.move_line_1 | self.move_line_2 | self.move_line_3 | self.move_line_4 | self.move_line_5
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        assert self.bank_reconcile.bank_reconcile_line_ids[0].current_balance == 0

    def test_check_current_balance_with_some_move_line(self):
        """
        Creo varias conciliaciones y chequeo si los balances son correctos
        """
        move_lines = self.move_line_1 | self.move_line_2 | self.move_line_3 | self.move_line_4
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        assert self.bank_reconcile.bank_reconcile_line_ids[0].current_balance == 100
        assert self.bank_reconcile.bank_reconcile_line_ids[0].last_balance == 0
        new_move_line_1 = self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Banco 1',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'credit': 1000,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        self.env['account.move.line'].with_context(check_move_validity=False).create({
            'name': 'Banco 1',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
            'debit': 1000,
            'date': '2017-08-24',
            'move_id': self.move.id
        })
        new_move_lines = new_move_line_1 | self.move_line_5
        active_ids = new_move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-15',
            'date_stop': '2017-08-16',
        })
        wizard.create_conciliation()
        assert self.bank_reconcile.bank_reconcile_line_ids[0].current_balance == -1000
        assert self.bank_reconcile.bank_reconcile_line_ids[0].last_balance == 100

    def test_check_date(self):
        """
        Chequeo rango de fechas, si ya existe una conciliacion mayor al rango de fechas dado
        muestra un error
        """
        move_lines = self.move_line_1 | self.move_line_2
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        new_move_lines = self.move_line_5 | self.move_line_3
        new_active_ids = new_move_lines.ids
        new_wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=new_active_ids).create({
            'date_start': '2017-07-20',
            'date_stop': '2017-08-01',
        })
        with self.assertRaises(ValidationError):
            new_wizard.create_conciliation()
        new_wizard.update({
            'date_start': '2017-08-20',
            'date_stop': '2017-08-30',
        })
        new_wizard.create_conciliation()

    def test_delete_last_reconcile(self):
        """
        Creo varias conciliaciones y luego intentamos eliminar la primer conciliacion
        al no ser la ultima conciliacion debe mostrar error
        """
        move_lines = self.move_line_1 | self.move_line_2
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        new_move_lines = self.move_line_5 | self.move_line_3
        new_active_ids = new_move_lines.ids
        new_wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=new_active_ids).create({
            'date_start': '2017-08-20',
            'date_stop': '2017-08-30',
        })
        new_wizard.create_conciliation()
        with self.assertRaises(ValidationError):
            self.bank_reconcile.bank_reconcile_line_ids[1].unlink()
        self.bank_reconcile.bank_reconcile_line_ids[0].unlink()

    def test_reconcile_delete_move(self):
        """
        Creo una conciliacion y luego intento eliminar un asiento de las lineas conciliadas
        """
        move_lines = self.move_line_1 | self.move_line_2 | self.move_line_3 | self.move_line_4 | self.move_line_5
        active_ids = move_lines.ids
        wizard = self.env['bank.reconcile.wizard'].with_context(active_ids=active_ids).create({
            'date_start': '2017-08-01',
            'date_stop': '2017-08-15',
        })
        wizard.create_conciliation()
        with self.assertRaises(IntegrityError):
            self.move.unlink()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

