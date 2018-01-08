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


class TestAccountThirdCheck(TestSoldCheck):

    def test_sold_check_id(self):
        self.sold_check.post()
        assert self.third_check.sold_check_id == self.sold_check

    def test_invalid_third_check_state(self):
        self.third_check.state = 'draft'
        with self.assertRaises(ValidationError):
            self.third_check.sold_check_ids = None

    def test_multiple_sold_checks(self):
        with self.assertRaises(ValidationError):
            self.env['account.sold.check'].create({
                'journal_id': self.sold_check.journal_id.id,
                'date': fields.Date.context_today(self.env['account.sold.check']),
                'account_third_check_ids': [(6, 0, [self.third_check.id])],
                'account_id': self.env.ref('l10n_ar.1_caja_pesos').id
            })

    def test_invalid_check_state_post(self):
        self.third_check.state = 'draft'
        with self.assertRaises(ValidationError):
            self.sold_check.post()

    def test_invalid_check_currency_post(self):
        usd = self.env.ref('base.USD')
        self.third_check.currency_id = usd.id
        third_checks = self.third_check | self.third_check_2
        with self.assertRaises(ValidationError):
            third_checks.post_sold_check()

    def test_invalid_check_state_cancel(self):
        self.third_check.state = 'draft'
        with self.assertRaises(ValidationError):
            self.sold_check.cancel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
