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
from openerp.exceptions import ValidationError, UserError


class TestAccountPayment(set_up.SetUp):

    def _create_checkbook_values(self):
        journal = self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos')
        own_check_line_proxy = self.env['account.own.check.line']
        date_today = fields.Date.context_today(own_check_line_proxy)
        journal.write({
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'bank_acc_number': 'Banco 1231',
            'update_posted': True
        })
        self.checkbook = self.env['account.checkbook'].create({
            'name': 'Chequera',
            'payment_type': 'postdated',
            'journal_id': journal.id,
            'number_from': '1',
            'number_to': '10',
        })
        own_check_proxy = self.env['account.own.check']
        self.own_check = own_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': self.checkbook.id
        })
        self.own_check_line = own_check_line_proxy.create({
            'own_check_id': self.own_check.id,
            'amount': 1250,
            'payment_type': 'postdated',
            'payment_date': date_today,
            'issue_date': date_today,
        })

    def setUp(self):
        super(TestAccountPayment, self).setUp()
        self._create_checkbook_values()

    def test_constrain_checks(self):
        # No deberia haber cheques de terceros ne pago a proveedores
        with self.assertRaises(ValidationError):
            self.supplier_payment.account_third_check_ids = self.third_check
        with self.assertRaises(ValidationError):
            self.customer_payment.account_own_check_line_ids = self.own_check_line

    def test_onchange_checks(self):

        # Probamos un pago de cliente
        self.customer_payment.account_third_check_ids = self.third_check
        self.customer_payment.onchange_account_third_check_ids()
        assert self.customer_payment.amount == self.third_check.amount

        # Probamos un pago de proveedor
        # Agregamos un cheque propio
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.supplier_payment.onchange_account_third_check_ids()
        assert self.supplier_payment.amount == self.own_check_line.amount
        # Agregamos un cheque de tercero
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.onchange_account_third_check_ids()
        assert self.supplier_payment.amount == self.own_check_line.amount+self.third_check.amount

    def test_payment_methods_customer_vals(self):
        self.customer_payment.account_third_check_ids = self.third_check
        vals = self.customer_payment.set_payment_methods_vals()
        # La cuenta de cheques de terceros debe salir de la compania
        assert vals[0].get('amount') == self.third_check.amount
        assert vals[0].get('account_id') == self.env.user.company_id.third_check_account_id.id

    def test_invalid_payment_methods_customer_vals(self):
        self.customer_payment.account_third_check_ids = self.third_check
        self.env.user.company_id.third_check_account_id = None
        with self.assertRaises(UserError):
            self.customer_payment.set_payment_methods_vals()

    def test_payment_methods_supplier_vals(self):
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        vals = self.supplier_payment.set_payment_methods_vals()
        vals.sort(key=lambda x: x['amount'])

        # En el caso de cheques propios debe salir de la chequera o del diario, probamos el caso del diario
        account = self.checkbook.journal_id.default_credit_account_id.id
        assert vals[0].get('account_id') == account
        caja_pesos = self.env.ref('l10n_ar.1_caja_pesos')
        # Probamos con la chequera ahora
        self.checkbook.account_id = caja_pesos
        vals = self.supplier_payment.set_payment_methods_vals()
        vals.sort(key=lambda x: x['amount'])

        assert vals[0].get('account_id') == caja_pesos.id
        assert vals[0].get('amount') == self.own_check_line.amount
        assert vals[1].get('account_id') == self.env.user.company_id.third_check_account_id.id
        assert vals[1].get('amount') == self.third_check.amount

    def test_invalid_payment_methods_supplier_vals(self):
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.checkbook.journal_id.default_credit_account_id = None
        with self.assertRaises(ValidationError):
            self.supplier_payment.set_payment_methods_vals()

    def test_post_supplier_payment(self):
        self.third_check.state = 'wallet'
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.supplier_payment.onchange_account_third_check_ids()
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)

        self.supplier_payment.post_l10n_ar()
        assert self.third_check.state == 'handed'
        assert self.own_check.state == 'handed'

    def test_post_invalid_supplier_payment(self):
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)
        self.supplier_payment.onchange_account_third_check_ids()

        # Intentamos validar el pago con el cheque propio en un estado invalido
        self.own_check.state = 'handed'
        with self.assertRaises(ValidationError):
            self.supplier_payment.post_l10n_ar()
        self.own_check.state = 'draft'

        # Intentamos validar el pago con el cheque de tercero en un estado invalido
        self.third_check.state = 'handed'
        with self.assertRaises(ValidationError):
            self.supplier_payment.post_l10n_ar()

    def test_post_customer_payment(self):
        self.customer_payment.account_third_check_ids = self.third_check
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.onchange_account_third_check_ids()
        self.customer_payment.post_l10n_ar()

        assert self.third_check.state == 'wallet'

    def test_post_customer_invalid_payment(self):
        self.customer_payment.account_third_check_ids = self.third_check
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.onchange_account_third_check_ids()
        self.third_check.state = 'wallet'
        with self.assertRaises(ValidationError):
            self.customer_payment.post_l10n_ar()

    def test_cancel_customer_payment(self):
        self.customer_payment.account_third_check_ids = self.third_check
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.onchange_account_third_check_ids()
        self.customer_payment.post_l10n_ar()
        self.customer_payment.cancel()
        assert self.third_check.state == 'draft'

    def test_cancel_supplier_payment(self):
        self.third_check.state = 'wallet'
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.supplier_payment.onchange_account_third_check_ids()
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)
        self.supplier_payment.post_l10n_ar()
        self.supplier_payment.cancel()

        assert self.third_check.state == 'wallet'
        assert self.own_check.state == 'draft'

    def test_cancel_invalid_customer_payment(self):
        self.customer_payment.account_third_check_ids = self.third_check
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.onchange_account_third_check_ids()
        self.customer_payment.post_l10n_ar()
        self.third_check.state = 'draft'

        with self.assertRaises(ValidationError):
            self.customer_payment.cancel()

    def test_cancel_invalid_supplier_payment(self):
        self.third_check.state = 'wallet'
        self.supplier_payment.account_third_check_sent_ids = self.third_check
        self.supplier_payment.account_own_check_line_ids = self.own_check_line
        self.supplier_payment.onchange_account_third_check_ids()
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)
        self.supplier_payment.post_l10n_ar()
        self.third_check.state = 'wallet'
        self.own_check.state = 'draft'

        with self.assertRaises(ValidationError):
            self.supplier_payment.cancel()

    def test_wizard_payment_vals(self):
        wizard = self.env['account.register.payments'].new()
        wizard.account_third_check_ids = self.third_check
        wizard.account_third_check_sent_ids = self.third_check
        wizard.account_own_check_line_ids = self.own_check_line
        vals = wizard.get_payment_vals()
        assert vals.get('account_third_check_ids') == [(4, self.third_check.id)]
        assert vals.get('account_third_check_sent_ids') == [(4, self.third_check.id)]
        assert vals.get('account_own_check_line_ids') == [(4, self.own_check_line.id)]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

