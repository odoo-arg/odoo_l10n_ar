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

import test_checkbook
from openerp import fields
from openerp.exceptions import ValidationError


class TestAccountOwnCheck(test_checkbook.TestCheckbook):

    def setUp(self):
        super(TestAccountOwnCheck, self).setUp()
        own_check_proxy = self.env['account.own.check']
        self.own_check = own_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': self.checkbook.id
        })

    def test_post_payment(self):
        # Cuando se valida un pago deberian pasar los cheques a cartera
        self.own_check.post_payment(None)
        assert self.own_check.state == 'handed'
        # No se deberia poder hacer esto si un cheque no esta en borrador
        with self.assertRaises(ValidationError):
            self.own_check.post_payment(None)

    def test_post_payment_with_vals(self):
        own_check_proxy = self.env['account.own.check']
        date_today = fields.Date.context_today(own_check_proxy)
        vals = {
            'amount': 300,
            'payment_date': date_today,
            'issue_date': date_today,
            'destination_payment_id': self.supplier_payment.id,
            'currency_id': self.supplier_payment.currency_id.id
        }
        self.own_check.post_payment(vals)
        assert self.own_check.amount == 300
        assert self.own_check.state == 'handed'

    def test_cancel_payment(self):
        # Cuando se cancel un pago deberian pasar los cheques a borrador
        self.own_check.post_payment(None)
        self.own_check.cancel_payment()
        assert self.own_check.state == 'draft'

        # No se deberia poder hacer esto si el cheque no esta en cartera
        with self.assertRaises(ValidationError):
            self.own_check.cancel_payment()

    def test_cancel_state(self):
        with self.assertRaises(ValidationError):
            self.own_check.cancel_state('invalid_state')

    def test_next_state(self):
        with self.assertRaises(ValidationError):
            self.own_check.next_state('invalid_state')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
