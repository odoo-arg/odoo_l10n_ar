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
from datetime import timedelta, datetime
from openerp import fields
from openerp.exceptions import ValidationError


class TestAccountCheck(set_up.SetUp):

    def test_invalid_check_name(self):
        with self.assertRaises(ValidationError):
            self.third_check.name = '123123A'

    def test_invalid_check_amount(self):
        with self.assertRaises(ValidationError):
            self.third_check.amount = -1
        with self.assertRaises(ValidationError):
            self.third_check.amount = 0
        self.third_check.amount = 0.1
        self.third_check.amount = 1000

    def test_check_dates(self):

        self.third_check.payment_date = self.third_check.issue_date
        # En un cheque comun no se deberia poder tener otra fecha de pago que no sea la de emision
        with self.assertRaises(ValidationError):
            self.third_check.payment_date =\
                datetime.strptime(self.third_check.issue_date, '%Y-%m-%d') + timedelta(days=1)
        self.third_check.payment_type = 'postdated'
        with self.assertRaises(ValidationError):
            self.third_check.payment_date = \
                datetime.strptime(self.third_check.issue_date, '%Y-%m-%d') - timedelta(days=1)
        self.third_check.payment_date = \
            datetime.strptime(self.third_check.issue_date, '%Y-%m-%d') + timedelta(days=1)

    def test_onchange_payment_type(self):
        third_check_proxy = self.env['account.third.check']
        third_check = third_check_proxy.new({
            'issue_date': fields.Date.context_today(third_check_proxy),
            'payment_type': 'common'
        })
        third_check.onchange_payment_type()
        assert third_check.issue_date == third_check.payment_date

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
