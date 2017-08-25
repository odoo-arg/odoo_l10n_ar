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


class TestAccountThirdCheck(set_up.SetUp):

    def test_destination_payment(self):
        self.third_check.account_payment_ids = self.customer_payment
        assert self.third_check.destination_payment_id == self.customer_payment

        # El cheque no deberia estar en paralelo en mas de un pago
        with self.assertRaises(ValidationError):
            self.third_check.account_payment_ids = [self.customer_payment.id, self.supplier_payment.id]

    def test_unlink(self):
        self.third_check.state = 'wallet'
        with self.assertRaises(ValidationError):
            self.third_check.unlink()
        self.third_check.state = 'draft'
        self.third_check.unlink()

    def test_post_receipt(self):
        # Si se valida un pago de cliente el cheque deberia pasarse a cartera y tener la moneda del pago
        self.third_check.post_receipt(self.customer_payment.currency_id.id)
        assert self.third_check.state == 'wallet'
        assert self.third_check.currency_id == self.customer_payment.currency_id
        # No se deberia poder hacer esto si el cheque no esta en borrador
        with self.assertRaises(ValidationError):
            self.third_check.post_receipt(self.customer_payment.currency_id.id)

    def test_cancel_receipt(self):
        # Si se cancela un pago de cliente el cheque deberia pasarse de vuelta a borrador
        self.third_check.post_receipt(self.customer_payment.currency_id.id)
        self.third_check.cancel_receipt()
        assert self.third_check.state == 'draft'
        # No se deberia poder hacer esto si el cheque no esta en cartera
        with self.assertRaises(ValidationError):
            self.third_check.cancel_receipt()

    def test_post_payment(self):
        self.third_check.post_receipt(self.customer_payment.currency_id.id)
        # Si se valida un pago de proveedor el cheque deberia pasarse de cartera a entregado
        self.third_check.post_payment()
        assert self.third_check.state == 'handed'
        # No se deberia poder hacer esto si el cheque no esta en cartera
        with self.assertRaises(ValidationError):
            self.third_check.post_payment()

    def test_cancel_payment(self):
        # Si se cancela un pago de proveedor el cheque deberia pasarse de vuelta a entregado
        self.third_check.post_receipt(self.customer_payment.currency_id.id)
        self.third_check.post_payment()
        self.third_check.cancel_payment()
        assert self.third_check.state == 'wallet'
        # No se deberia poder hacer esto si el cheque no esta en cartera
        with self.assertRaises(ValidationError):
            self.third_check.cancel_payment()

    def test_cancel_invalid_state(self):
        with self.assertRaises(ValidationError):
            self.third_check.cancel_state('invalid_state')

    def test_invalid_next_state(self):
        with self.assertRaises(ValidationError):
            self.third_check.next_state('invalid_state')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
