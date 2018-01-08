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

from odoo.addons.l10n_ar_account_payment.tests import set_up


class TestAccountRegisterPayments(set_up.SetUp):

    def setUp(self):
        super(TestAccountRegisterPayments, self).setUp()
        self.imputation = self.env['payment.imputation.line'].create({
            'invoice_id': self.invoice.id,
            'payment_id': self.customer_payment.id,
        })
        self.payment_wizard = self.env['account.register.payments']. \
            with_context(active_ids=self.invoice.id, active_model='account.invoice').create({
                'partner_id': self.partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'amount': 500,
                'payment_type_line_ids': [(6, 0, [self.payment_line.id])],
                'payment_imputation_ids': [(6, 0, [self.imputation.id])]
            })

    def test_get_payment_vals(self):
        res = self.payment_wizard.get_payment_vals()
        assert res.get('payment_imputation_ids') == [(4, self.imputation.id)]

    def test_onchange_partner(self):
        self.payment_wizard.payment_imputation_ids = None
        self.payment_wizard.onchange_partner_imputation()
        assert len(self.payment_wizard.payment_imputation_ids) == 1

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
