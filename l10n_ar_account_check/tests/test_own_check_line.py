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
from openerp import fields
from openerp.exceptions import ValidationError
from datetime import timedelta, datetime


class TestOwnCheckLine(set_up.SetUp):

    def setUp(self):
        super(TestOwnCheckLine, self).setUp()

        own_check_line_proxy = self.env['account.own.check.line']
        date_today = fields.Date.context_today(own_check_line_proxy)
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        journal.write({
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'bank_acc_number': 'Banco 1231'
        })
        self.checkbook_line = self.env['account.checkbook'].create({
            'name': 'Chequera',
            'payment_type': 'postdated',
            'journal_id': journal.id,
            'number_from': '1',
            'number_to': '10',
        })
        self.line_own_check = self.env['account.own.check'].create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': self.checkbook_line.id
        })
        self.own_check_line = own_check_line_proxy.create({
            'own_check_id': self.line_own_check.id,
            'amount': 1250,
            'payment_type': 'postdated',
            'payment_date': date_today,
            'issue_date': date_today,
        })

    def test_post_payment_with_a_different_currency(self):
        self.own_check_line.own_check_id.currency_id = self.env.ref('base.ARS')
        self.supplier_payment.currency_id = self.env.ref('base.USD')
        with self.assertRaises(ValidationError):
            self.own_check_line.post_payment(self.supplier_payment)

    def test_post_payment_with_same_currency(self):
        self.own_check_line.own_check_id.currency_id = self.env.ref('base.ARS')
        self.supplier_payment.currency_id = self.env.ref('base.ARS')
        self.own_check_line.post_payment(self.supplier_payment)

    def test_post_payment(self):
        """ Probamos que los valores de las lineas de cheques propios asigne los valores correctamente """

        self.own_check_line.post_payment(self.supplier_payment)
        assert self.line_own_check.amount == self.own_check_line.amount
        assert self.line_own_check.payment_date == self.own_check_line.payment_date
        assert self.line_own_check.issue_date == self.own_check_line.issue_date
        assert self.line_own_check.id == self.own_check_line.own_check_id.id
        assert self.line_own_check.payment_type == self.own_check_line.payment_type
        assert self.line_own_check.destination_payment_id == self.supplier_payment

    def test_constraint_own_check(self):
        self.own_check_line.payment_id = self.supplier_payment.id
        with self.assertRaises(ValidationError):
            self.own_check_line.create({
                'own_check_id': self.line_own_check.id,
                'amount': 20,
                'payment_id': self.supplier_payment.id
            })

    def test_onchange_checkbook(self):
        """ Probamos el domain de cheques cuando se selecciona o deselecciona una chequera """

        # Si se selecciona una chequera, deben aparecer los cheques de esa chequera en borrador """
        own_check_line = self.env['account.own.check.line'].new(self.own_check_line.read()[0])
        own_check_line.checkbook_id = self.checkbook_line.id
        res = own_check_line.onchange_checkbook()
        domain = [
            ('destination_payment_id', '=', False),
            ('state', '=', 'draft'),
            ('checkbook_id', '=', self.checkbook_line.id)
        ]
        assert res == {'domain': {'own_check_id': domain}}

        # Si no tiene chequera, deberian aparecer todos los cheques sin pago, en borrador
        own_check_line.checkbook_id = None
        res = own_check_line.onchange_checkbook()
        domain = [
            ('destination_payment_id', '=', False),
            ('state', '=', 'draft'),
        ]
        assert res == {'domain': {'own_check_id': domain}}

    def test_onchange_check(self):
        own_check_line = self.env['account.own.check.line'].new(self.own_check_line.read()[0])
        assert (own_check_line.payment_date and own_check_line.issue_date and own_check_line.amount)
        own_check_line.onchange_own_check()
        assert not(own_check_line.payment_date and own_check_line.issue_date and own_check_line.amount)

    def test_onchange_issue_date(self):
        self.own_check_line.write({
            'payment_type': 'common',
            'payment_date': None
        })
        own_check_line = self.own_check_line.new(self.own_check_line.read()[0])
        self.own_check_line.onchange_issue_date()
        assert self.own_check_line.payment_date == self.own_check_line.issue_date
        own_check_line.issue_date = None
        own_check_line.onchange_issue_date()
        assert not own_check_line.payment_date

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
