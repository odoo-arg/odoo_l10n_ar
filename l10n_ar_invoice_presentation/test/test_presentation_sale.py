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


class TestPresentationSale(TransactionCase):
    @staticmethod
    def _create(proxy, dictionary):
        created = proxy.sudo().create(dictionary)
        return created

    def setUp(self):
        # calleamos al super
        super(TestPresentationSale, self).setUp()
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

    def test_sale_invoice_presentation(self):
        b64 = self.account_invoice_presentation.generate_sale_file()
        decoded = base64.decodestring(b64.get_encoded_string())
        # Fecha de comprobante
        assert decoded[0:8] == "20000801"
        # Tipo de comprobante
        assert decoded[8:11] == "001"
        # Punto de venta
        assert decoded[11:16] == "00001"
        # Numero de comprobante
        assert decoded[16:36] == "00000000000000000008"
        # Numero de comprobante hasta
        assert decoded[36:56] == "00000000000000000008"
        # Codigo de documento del comprador
        assert decoded[56:58] == "80"
        # Numero de identificacion del comprador
        assert decoded[58:78] == "00000000020307810795"
        # Apellido y nombre del comprador
        assert decoded[78:108] == "Test Partner                  "
        # Importe total de la operacion
        assert decoded[108:123] == "000000000121000"
        # Importe total de conceptos que no integran el precio neto gravado
        assert decoded[123:138] == "000000000000000"
        # Percepcion a no categorizados
        assert decoded[138:153] == "000000000000000"
        # Importe de operaciones exentas
        assert decoded[153:168] == "000000000000000"
        # Importe de percepciones o pagos a cuenta de impuestos nacionales
        assert decoded[168:183] == "000000000000000"
        # Importe de percepciones de ingresos brutos
        assert decoded[183:198] == "000000000000000"
        # Importe de percepciones impuestos municipales
        assert decoded[198:213] == "000000000000000"
        # Importe impuestos internos
        assert decoded[213:228] == "000000000000000"
        # Codigo de moneda
        assert decoded[228:231] == "PES"
        # Tipo de cambio
        assert decoded[231:241] == "0001000000"
        # Cantidad de alicuotas de IVA
        assert decoded[241:242] == "1"
        # Codigo de operacion
        assert decoded[242:243] == " "
        # Otros tributos
        assert decoded[243:258] == "000000000000000"
        # Fecha de vencimiento de pago
        assert decoded[258:266] == "20000801"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
