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
from openerp.tests.common import TransactionCase

from odoo.exceptions import ValidationError


class RetentionPartnerRuleTest(TransactionCase):
    # ---
    # AUX
    # ---
    def find_retentions(self):
        self.profit_retention = self.env['retention.retention'].search([('type', '=', 'profit')], limit=1)
        self.non_profit_retention = self.env['retention.retention'].search([('type', '!=', 'profit')], limit=1)

    def find_activity(self):
        self.activity = self.env['retention.activity'].search([], limit=1)

    def find_currency(self):
        self.currency = self.env['res.currency'].search([], limit=1)

    def find_journal(self):
        self.journal = self.env['account.journal'].search([], limit=1)

    def find_payment_method(self):
        self.payment_method = self.env['account.payment.method'].search([], limit=1)

    def create_partner(self):
        self.partner = self.env['res.partner'].create({
            'name': "Partner",
        })

    def create_payment(self):
        self.payment = self.env['account.payment'].create({
            'currency_id': self.currency.id,
            'journal_id': self.journal.id,
            'payment_method_id': self.payment_method.id,
            'amount': 5,
            'payment_type': 'inbound',
        })

    # -----
    # SETUP
    # -----
    def setUp(self):
        super(RetentionPartnerRuleTest, self).setUp()
        self.find_retentions()
        self.find_activity()
        self.find_currency()
        self.find_journal()
        self.find_payment_method()
        self.create_partner()
        self.create_payment()
        self.payment.retention_ids.unlink()

    # -----
    # TESTS
    # -----
    def test_repeated_rule(self):
        self.env['account.payment.retention'].create({
            'name': "R",
            'jurisdiction': 'nacional',
            'amount': 5,
            'payment_id': self.payment.id,
            'retention_id': self.profit_retention.id,
            'activity_id': self.activity.id,
        })
        with self.assertRaises(ValidationError):
            self.env['account.payment.retention'].create({
                'name': "R",
                'jurisdiction': 'nacional',
                'amount': 5,
                'payment_id': self.payment.id,
                'retention_id': self.profit_retention.id,
                'activity_id': self.activity.id,
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
