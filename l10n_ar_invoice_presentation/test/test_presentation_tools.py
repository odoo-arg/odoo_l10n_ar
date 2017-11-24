# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from datetime import datetime
from openerp.tests.common import TransactionCase
from ..models.presentation_tools import PresentationTools

class TestTools(TransactionCase):
    def create_product(self):
        return self.env['product.product'].create({
            "name": "Test Consumable Product",
            "type": "consu",
            "standard_price": 1000,
            "supplier_taxes_id": [(6, 0, [self.env.ref("l10n_ar.1_vat_21_compras").id])]
        })

    def create_partner(self, is_aduana=False):
        data = {
            "name": "Test Partner",
            "vat": "20307810795",
            "supplier": True,
            "customer": True,
            "partner_document_type_id": self.env.ref("l10n_ar_afip_tables.partner_document_type_80").id,
            "country_id": self.env.ref("base.ar").id,
        }
        if is_aduana:
            data.update({"property_account_position_id": self.fiscal_position_ad.id})
        else:
            data.update({"property_account_position_id": self.fiscal_position_ri.id})

        return self.env['res.partner'].create(data)

    def create_invoice_line(self, invoice, product):
        return self.env['account.invoice.line'].create({
            "name": "Test Consumable Product",
            "product_id": product.id,
            "price_unit": 1000,
            "account_id": product.categ_id.property_account_expense_categ_id.id,
            "invoice_id": invoice.id,
            "invoice_line_tax_ids": [(6, 0, [self.env.ref("l10n_ar.1_vat_21_compras").id])]
        })

    def create_invoice(self):
        partner = self.create_partner()
        product = self.create_product()
        invoice = self.env['account.invoice'].create({
            "name": '0001-00000001',
            "partner_id": partner.id,
            "type": "in_invoice",
            "date_invoice": "2017-08-01",
            "currency_id": self.env.ref("base.USD").id
        })
        # Ejecuto onchange de partner
        invoice.onchange_partner_id()

        # Creo linea y ejecuto onchange de producto
        invoice_line = self.create_invoice_line(invoice, product)
        invoice_line._onchange_product_id()

        # Ejecuto onchange de lineas y valido
        invoice._onchange_invoice_line_ids()
        invoice.action_invoice_open()

        return invoice

    def get_general_data(self):
        self.fiscal_position_ri = self.env.ref("l10n_ar_afip_tables.account_fiscal_position_ivari")

    def setUp(self):
        super(TestTools, self).setUp()
        self.get_general_data()
        self.env.user.company_id.partner_id.property_account_position_id = self.fiscal_position_ri

    def test_get_currency(self):
        """
        Se testea la herramienta de obtener currency
        """
        self.env['res.currency.rate'].create({
            'name': datetime(2016, 9, 8, 11, 8, 40, 10956),
            'currency_id': self.env.ref('base.USD').id,
            'rate': 0.2
        })
        invoice = self.create_invoice()

        currency = PresentationTools.get_currency_rate_from_move(invoice)
        assert currency == 5.0


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
