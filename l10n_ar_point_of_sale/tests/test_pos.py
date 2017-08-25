
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

from psycopg2._psycopg import IntegrityError
from openerp.exceptions import ValidationError
from test_document_book import TestDocumentBook


class TestPos(TestDocumentBook):

    def setUp(self):
        super(TestPos, self).setUp()

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            self.pos_proxy.create({
                'name': 5,
                'sequence': -50
            })

    def test_name_of_pos(self):
        assert self.pos.name_get()[0][1] == '0005'
        with self.assertRaises(ValidationError):
            self.pos.name = 'pos'

    def test_get_pos(self):
        self.pos_proxy.get_pos('invoice', self.env.ref('l10n_ar_afip_tables.account_denomination_a'))
        with self.assertRaises(ValidationError):
            self.pos_proxy.get_pos('payment', self.env.ref('l10n_ar_afip_tables.account_denomination_i'))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
