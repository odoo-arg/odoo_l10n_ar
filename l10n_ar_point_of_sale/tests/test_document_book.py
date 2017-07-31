
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
from psycopg2._psycopg import IntegrityError
from openerp.exceptions import ValidationError


class TestDocumentBook(common.TransactionCase):

    def setUp(self):
        super(TestDocumentBook, self).setUp()
        # Proxies
        self.iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        self.document_book_proxy = self.env['document.book']
        self.pos_proxy = self.env['pos.ar']

        # Configuracion de posicion fiscal RI en la compania
        self.env.user.company_id.partner_id.property_account_position_id = self.iva_ri

        self.pos = self.pos_proxy.create({'name': 5})
        self.document_book = self.document_book_proxy.create({
            'name': 32,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_point_of_sale.account_denomination_a').id,
        })

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            self.document_book_proxy.create({
                'name': 1,
                'pos_ar_id': self.pos.id,
                'category': 'invoice',
                'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_picking').id,
                'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
                'denomination_id': self.env.ref('l10n_ar_point_of_sale.account_denomination_a').id,
            })

    def test_name_of_document_book(self):
        assert self.document_book.name_get()[0][1] == '00000032'
        with self.assertRaises(ValidationError):
            self.document_book.name = 'op'

    def test_next_number(self):
        assert self.document_book.next_number() == '0005-00000033'

    def test_document_book_type(self):
        self.document_book.book_type_id._get_name()
        assert self.document_book.book_type_id.name == 'Preimpreso'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
