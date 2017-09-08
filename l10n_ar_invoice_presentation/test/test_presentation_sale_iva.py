# coding: utf-8
##############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
import base64
from openerp.tests.common import TransactionCase


class TestPresentationSaleIva(TransactionCase):
    @staticmethod
    def _create(proxy, dictionary):
        created = proxy.sudo().create(dictionary)
        return created

    def setUp(self):
        # calleamos al super
        super(TestPresentationSaleIva, self).setUp()
        # creamos los proxies necesarios
        pos_ar_proxy = self.env["pos.ar"]
        res_partner_proxy = self.env["res.partner"]
        product_product_proxy = self.env["product.product"]
        account_invoice_proxy = self.env["account.invoice"]
        account_invoice_line_proxy = self.env["account.invoice.line"]
        account_invoice_presentation_proxy = self.env["account.invoice.presentation"]
        # traemos la posicion fiscal iva responsable inscripto
        iva_r_i = self.env.ref("l10n_ar_afip_tables.account_fiscal_position_ivari")
        # seteamos la posicion fiscal en el partner y en la compania
        self.env.user.company_id.partner_id.property_account_position_id = iva_r_i.id
        self.company_fiscal_position = self.env.user.company_id.partner_id.property_account_position_id
        # creamos el punto de venta
        self.pos_ar = self._create(pos_ar_proxy, {
            "name": "0007"
        })
        # creamos el partner
        self.res_partner = self._create(res_partner_proxy, {
            "name": "Test Partner",
            "vat": "20307810795",
            "supplier": True,
            "customer": True,
            "partner_document_type_id": self.env.ref("l10n_ar_afip_tables.partner_document_type_80").id,
            "country_id": self.env.ref("base.ar").id,
            "property_account_position_id": self.company_fiscal_position.id
        })
        # creamos el producto
        self.product_product = self._create(product_product_proxy, {
            "name": "Test Consumable Product",
            "type": "consu",
            "taxes_id": [(6, 0, [self.env.ref("l10n_ar.1_vat_21_ventas").id])]
        })
        # creamos el punto de venta
        pos = self.env["pos.ar"].create({
            "name": "9"
        })
        # creamos el talonario para la factura
        self.env["document.book"].create({
            "name": "1",
            "category": "invoice",
            "pos_ar_id": pos.id,
            "book_type_id": self.env.ref("l10n_ar_point_of_sale.document_book_type_preprint_invoice").id,
            "document_type_id": self.env.ref("l10n_ar_point_of_sale.document_type_invoice").id,
            "denomination_id": self.env.ref("l10n_ar_afip_tables.account_denomination_a").id
        })
        # creamos la factura
        self.account_invoice = self._create(account_invoice_proxy, {
            "partner_id": self.res_partner.id,
            "type": "out_invoice",
            "date_invoice": "2000-08-01"
        })
        # llamamos al onchange
        self.account_invoice.onchange_partner_id()
        # creamos la linea de la factura
        self.account_invoice_line = self._create(account_invoice_line_proxy, {
            "name": "Test Consumable Product",
            "product_id": self.product_product.id,
            "price_unit": 0,
            "account_id": self.product_product.categ_id.property_account_income_categ_id.id,
            "invoice_id": self.account_invoice.id
        })
        # llamamos al onchange
        self.account_invoice_line._onchange_product_id()
        # cambiamos el precio unitario del producto
        self.account_invoice_line.price_unit = 1000
        # llamamos al onchange
        self.account_invoice._onchange_invoice_line_ids()
        # validamos la factura
        self.account_invoice.action_invoice_open()
        # le mandamo viaje al numero de la factura
        self.account_invoice.name = "0001-00000008"
        # creamos la presentacion
        self.account_invoice_presentation = self._create(account_invoice_presentation_proxy, {
            "name": "test",
            "date_from": "2000-08-01",
            "date_to": "2000-08-31",
            "sequence": "00",
            "with_prorate": False
        })

    def test_sale_vat_invoice_presentation(self):
        b64 = self.account_invoice_presentation.generate_sale_vat_file()
        decoded = base64.decodestring(b64.get_encoded_string())
        # Tipo de comprobante
        assert decoded[0:3] == "001"
        # Punto de venta
        assert decoded[3:8] == "00001"
        # Numero de comprobante
        assert decoded[8:28] == "00000000000000000008"
        # Importe neto gravado
        assert decoded[28:43] == "000000000100000"
        # Alicuota de iva
        assert decoded[43:47] == "0005"
        # Impuesto liquidado
        assert decoded[47:62] == "000000000021000"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
