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

from odoo.tests import common
from openerp.exceptions import ValidationError

class TestAccountDocumentTax(common.TransactionCase):

    def setUp(self):
        super(TestAccountDocumentTax, self).setUp()
        self.document_tax = self.env['account.document.tax'].new({})

    def test_check_amount_with_amount_zero(self):
        self.document_tax.amount = 0.0
        with self.assertRaises(ValidationError):
            self.document_tax.check_amount()

    def test_check_amount_with_amount_negative(self):
        self.document_tax.amount = -10.0
        with self.assertRaises(ValidationError):
            self.document_tax.check_amount()

    def test_check_amount_with_amount_positive(self):
        self.document_tax.amount = 10.0
        self.document_tax.check_amount()

    def test_check_base_with_amount_zero(self):
        self.document_tax.base = 0.0
        self.document_tax.check_base()

    def test_check_base_with_amount_negative(self):
        self.document_tax.base = -10.0
        with self.assertRaises(ValidationError):
            self.document_tax.check_base()

    def test_check_base_with_amount_positive(self):
        self.document_tax.base = 10.0
        self.document_tax.check_base()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
