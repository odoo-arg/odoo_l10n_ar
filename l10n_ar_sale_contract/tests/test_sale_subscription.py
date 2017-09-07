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

class TestSaleSubscription(common.TransactionCase):

    def setUp(self):
        super(TestSaleSubscription, self).setUp()

    def test_create_invoice_from_subscription(self):

        # CONFIGURO LA EMPRESA COMO RI, UN PARTNER COMO RI
        # Y CREO PUNTO DE VENTA Y TALONARIO CON DENOMINACION
        # A PARA FACTURAS.

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
            'name': 'Cliente A',
            'property_account_position_id': iva_ri.id
        })
        product = self.env['product.product'].create({
            'name': 'Producto A',
            'list_price': 100.0
        })

        # SUBSCRIPCION

        subscription_template = self.env['sale.subscription.template'].create({
            'name': 'PLANTILLA TEST',
            'subscription_template_line_ids': [(0, 0, {
                'name': product.name,
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'quantity': 2,
            })],
        })

        subscription = self.env['sale.subscription'].create({
            'partner_id': partner.id,
            'template_id': subscription_template.id,
            'pricelist_id': self.env.ref('product.list0').id,

        })

        subscription.onchange_partner_id()
        subscription.on_change_template()

        invoices = subscription._recurring_create_invoice()
        
        for invoice in invoices:

            assert invoice.denomination_id == denomination_a

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: