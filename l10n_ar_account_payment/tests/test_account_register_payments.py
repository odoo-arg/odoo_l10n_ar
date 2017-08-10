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
from openerp.exceptions import ValidationError


class TestAccountRegisterPayments(set_up.SetUp):

    def setUp(self):
        super(TestAccountRegisterPayments, self).setUp()
        self.payment_wizard = self.env['account.register.payments'].\
            with_context(active_ids=self.invoice.id, active_model='account.invoice').create({
                'partner_id': self.partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'amount': 500,
                'payment_type_line_ids': [(6, 0, [self.payment_line.id])]
            })

    def test_old_payment_from_wizard(self):
        with self.assertRaises(ValidationError):
            self.payment_wizard.create_payment()

    def test_payment_from_wizard(self):
        self.payment_wizard.create_payment_l10n_ar()

    def test_payment_vals(self):
        payment_vals = self.payment_wizard.get_payment_vals()
        assert payment_vals.get('payment_type_line_ids')[0][1] == self.payment_line.id
        assert payment_vals.get('pos_ar_id') == self.pos_inbound.id

    def test_invalid_invoice(self):
        self.invoice.state = 'draft'
        with self.assertRaises(ValidationError):
            self.payment_wizard.create_payment_l10n_ar()

