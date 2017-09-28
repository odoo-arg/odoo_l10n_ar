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

from odoo.addons.l10n_ar_account_paymenttests import set_up


class TestPaymentImputation(set_up.SetUp):

    def setUp(self):
        super(TestPaymentImputation, self).setUp()
        self.imputation = self.env['payment.imputation.line'].create({
            'invoice_id': self.invoice.id,
            'payment_id': self.customer_payment.id,
        })

    def test_reconcile_invoices(self):

        self.customer_payment.pos_ar_id = self.pos_inbound
        self.customer_payment.post_l10n_ar()
        move_line = self.env['account.move.line'].search([('payment_id', '=', self.id)]).\
            filtered(lambda x: x.account_id.type == 'receivable')

        self.customer_payment.reconcile_invoices(move_line)
        self.imputation.amount = 500
        assert self.invoice.residual == 710

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
