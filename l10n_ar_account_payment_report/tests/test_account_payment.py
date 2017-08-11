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

from odoo.tests.common import TransactionCase
from openerp.exceptions import ValidationError


class TestAccountPayment(TransactionCase):

    def setUp(self):
        super(TestAccountPayment, self).setUp()
        self.payments = []
        self._create_all()

    def _create_payment(self):
        payment_proxy = self.env['account.payment']
        if not self.payments:
            payment_1 = payment_proxy.new({'id': 1, 'name': 'TEST BORRADOR', 'amount': 100, 'state': 'draft'})
            payment_2 = payment_proxy.new({'id': 2, 'name': 'TEST POSTED', 'amount': 200, 'state': 'posted'})
            self.payments = [payment_1, payment_2]

    def _create_all(self):
        self._create_payment()

    def test_check_state_draft(self):
        report = self.env['report.l10n_ar_account_payment_report.report_account_payment'].new({})
        payments = self.payments
        with self.assertRaises(ValidationError):
            report._validate_state(payments[0])

    def test_check_state_posted(self):
        report = self.env['report.l10n_ar_account_payment_report.report_account_payment'].new({})
        payments = self.payments
        report._validate_state(payments[1])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
