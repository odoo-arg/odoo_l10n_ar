
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

from openerp.exceptions import UserError
from test_document_book import TestDocumentBook


class TestPos(TestDocumentBook):

    def setUp(self):
        super(TestPos, self).setUp()

    def test_get_denomination(self):
        iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        iva_ext = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_cliente_ext')
        assert iva_ri.get_denomination(iva_ri) == self.env.ref('l10n_ar_point_of_sale.account_denomination_a')
        assert iva_ri.get_denomination(iva_ext) == self.env.ref('l10n_ar_point_of_sale.account_denomination_e')
        with self.assertRaises(UserError):
            iva_ri.get_denomination(self.env.ref('l10n_ar_point_of_sale.account_denomination_i')).get_denomination()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
