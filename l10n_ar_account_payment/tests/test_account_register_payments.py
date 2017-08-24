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

import simplejson
import set_up
from openerp.exceptions import ValidationError


class TestAccountRegisterPayments(set_up.SetUp):

    def setUp(self):
        super(TestAccountRegisterPayments, self).setUp()
        self.payment_wizard = self.env['account.register.payments']. \
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

    def test_invoice_outsanding_widget_info_payment_inbound(self):
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.customer_payment.post_l10n_ar()
        outstanding_credits = simplejson.loads(self.invoice.outstanding_credits_debits_widget)
        contents = outstanding_credits.get('content')
        assert contents[0].get('journal_name') == 'REC '+self.customer_payment.name[-8:]

    def test_invoice_outsanding_widget_info_payment_outbound(self):

        # Cambiamos la factura del setUp a proveedor
        self.invoice.journal_id.update_posted = True
        self.invoice.action_invoice_cancel()
        self.invoice.write({
            'type': 'in_invoice',
            'state': 'draft'
        })
        self.invoice.onchange_partner_id()
        self.invoice._onchange_partner_id()
        self.invoice.action_invoice_open()

        # Validamos el pago a proveedor
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)
        self.payment_line.payment_id = self.supplier_payment.id
        self.supplier_payment.post_l10n_ar()

        # Validamos la informacion del widget
        self.invoice._get_outstanding_info_JSON()
        outstanding_credits = simplejson.loads(self.invoice.outstanding_credits_debits_widget)
        contents = outstanding_credits.get('content')
        assert contents[0].get('journal_name') == 'OP ' + self.supplier_payment.name[-8:]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
