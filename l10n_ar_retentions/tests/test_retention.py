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
from lxml import etree


class TestRetention(common.TransactionCase):

    def _get_fields_view_get(self, **kwargs):

        res = self.payment.with_context(kwargs).fields_view_get(
            view_id=kwargs.get('view_id'),
            view_type='form',
            toolbar=kwargs.get('toolbar'),
            submenu=False
        )

        arch = res['fields']['retention_ids']['views']['tree']['arch']
        return etree.XML(arch)

    def _create_invoices(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        pos = self.env['pos.ar'].create({'name': 5})
        self.env['document.book'].create({
            'name': 1,
            'pos_ar_id': pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })
        self.product_21_consu = self.env['product.product'].create({
            'name': '21 consu',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.env.ref('l10n_ar.1_vat_21_ventas').id])]
        })
        self.invoice = invoice_proxy.create({
            'partner_id': self.partner.id,
            'type': 'out_invoice'
        })
        self.invoice.onchange_partner_id()
        invoice_line = invoice_line_proxy.create({
            'name': 'product_21_test',
            'product_id': self.product_21_consu.id,
            'price_unit': 0,
            'account_id': self.product_21_consu.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.invoice.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 1000
        self.invoice._onchange_invoice_line_ids()
        self.invoice.action_invoice_open()

    def setUp(self):
        super(TestRetention, self).setUp()
        # Configuracion de posicion fiscal RI en la compania
        iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        self.env.user.company_id.partner_id.property_account_position_id = iva_ri
        self.retention_caba = self.env.ref('l10n_ar_retentions.retention_retention_iibb_caba_efectuada')
        self.payment = self.env['account.payment'].create({
            'company_id': self.env.user.company_id.id,
            'amount': 10,
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'payment_type': 'inbound',
        })
        self.retention_payment = self.env['account.payment.retention'].create({
            'retention_id': self.retention_caba.id,
            'payment_id': self.payment.id,
            'name': self.retention_caba.name,
            'jurisdiction': self.retention_caba.jurisdiction,
            'amount': 50,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'supplier': True,
            'customer': True,
            'property_account_position_id': self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id,
        })
        self._create_invoices()

    def test_onchange_retention(self):
        retention_payment = self.env['account.payment.retention'].new(self.retention_payment.read()[0])
        # Con retencion asignada
        retention_payment.onchange_retention_id()
        assert retention_payment.name == self.retention_caba.name
        assert retention_payment.jurisdiction == self.retention_caba.jurisdiction

        # Sin retencion asignada
        retention_payment.retention_id = None
        retention_payment.onchange_retention_id()
        assert not retention_payment.name
        assert not retention_payment.jurisdiction

    def test_onchange_retentions(self):
        self.payment.onchange_retention_ids()
        assert self.payment.amount == self.retention_payment.amount

    def test_set_payment_method_vals(self):
        vals = self.payment.set_payment_methods_vals()
        assert vals[0].get('amount') == 50
        assert vals[0].get('account_id') == self.retention_caba.tax_id.account_id.id

    def test_get_payment_method_vals_wizard(self):
        payment_wizard = self.env['account.register.payments'].\
            with_context(active_ids=self.invoice.id, active_model='account.invoice').create({
                'partner_id': self.partner.id,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'amount': 500,
                'retention_ids': [(6, 0, [self.retention_payment.id])]
            })
        res = payment_wizard.get_payment_vals()
        assert res.get('retention_ids')[0][0] == self.retention_caba.id

    def test_view_get_payment(self):
        """ Probamos desde pago de clientes/proveedores """

        doc = self._get_fields_view_get(default_payment_type='inbound', toolbar=True)
        # Si en el contexto tenemos default_payment_type, deberia estar el domain del tipo de pago si no es interno
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','sale')]"

        doc = self._get_fields_view_get(default_payment_type='outbound', toolbar=True)
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','purchase')]"

        # Probamos con el interno
        doc = self._get_fields_view_get(default_payment_type='transfer', toolbar=True)
        for node in doc.xpath("//field[@name='retention_id']"):
            assert not node.get('domain')

    def test_view_get_payment_invoice(self):
        """ Probamos desde un pago a una factura con el boton registrar pago """

        view_id = self.env.ref('account.view_account_payment_invoice_form').id

        doc = self._get_fields_view_get(view_id=view_id, type='inbound')
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','sale')]"

        doc = self._get_fields_view_get(default_payment_type='outbound')
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','purchase')]"

    def test_view_get_payment_invoice_from_wizard(self):
        """ Probamos desde un pago a una factura desde el wizard de pago """

        doc = self._get_fields_view_get(active_id=self.invoice.id, active_model='account.invoice')
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','sale')]"

        self.invoice.type = 'in_invoice'
        doc = self._get_fields_view_get(active_id=self.invoice.id, active_model='account.invoice')
        for node in doc.xpath("//field[@name='retention_id']"):
            assert node.get('domain') == "[('type_tax_use', '=','purchase')]"

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
