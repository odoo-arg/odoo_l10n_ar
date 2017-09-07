
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
from openerp.exceptions import ValidationError, UserError
from datetime import datetime

class TestSaleOrder(common.TransactionCase):

    def setUp(self):
        super(TestSaleOrder, self).setUp()

    def test_create_invoice_without_lines_from_sale_order(self):
        sale = self.env['sale.order'].new({})
        with self.assertRaises(UserError):
            sale.action_invoice_create()

    def test_create_invoice_from_sale_order(self):

        iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')

        denomination_a = self.env.ref('l10n_ar_afip_tables.account_denomination_a')

        self.env.user.company_id.partner_id.property_account_position_id = iva_ri

        pos = self.env['pos.ar'].create({'name': 5})

        self.env['document.book'].create({
            'name': 32,
            'pos_ar_id': pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': denomination_a.id,
        })

        partner = self.env['res.partner'].create({
            'name':'Cliente A',
            'property_account_position_id': iva_ri.id
        })

        product = self.env['product.product'].create({
            'name': 'Producto A',
            'list_price': 100.0
        })

        sale = self.env['sale.order'].create({
            'partner_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'date_order': datetime.today(),
            'order_line': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'product_uom_qty': 2,
                'product_uom': product.uom_id.id,
                'price_unit': product.list_price,
                'qty_to_invoice': 2,
                })
            ],

        })

        sale.onchange_partner_id()

        sale.action_confirm()

        inv_ids = sale.action_invoice_create()

        assert self.env['account.invoice'].browse(inv_ids).denomination_id == denomination_a

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: