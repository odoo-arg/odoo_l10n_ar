
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
import json


class TestInvoice(common.TransactionCase):

    def _create_partners(self):
        self.partner_ri = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
            'supplier': True,
            'property_account_position_id': self.iva_ri.id
        })

    def _create_invoices(self):
        account = self.partner_ri.property_account_receivable_id
        self.pos = self.pos_proxy.create({'name': 5})
        self.document_book = self.document_book_proxy.create({
            'name': 10,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_ri.id,
            'fiscal_position_id': self.partner_ri.property_account_position_id.id,
            'account_id': account.id,
            'type': 'out_invoice',
            'state': 'draft'
        })

    def _create_invoice_lines(self):
        account = self.partner_ri.property_account_receivable_id
        self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 1,
            'price_unit': 500,
            'invoice_id': self.invoice.id,
        })

    def _create_invoice_line_with_vat(self):
        account = self.partner_ri.property_account_receivable_id
        vat_21 = self.env.ref('l10n_ar.1_vat_21_ventas').id
        return self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 1,
            'invoice_line_tax_ids': [(6, 0, [vat_21])],
            'price_unit': 1000,
            'invoice_id': self.invoice.id,
        })

    def _create_invoice_line_with_exempt_tax(self):
        account = self.partner_ri.property_account_receivable_id
        vat_ex = self.env.ref('l10n_ar.1_vat_exento_ventas').id
        self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 2,
            'invoice_line_tax_ids': [(6, 0, [vat_ex])],
            'price_unit': 750,
            'invoice_id': self.invoice.id,
        })

    def setUp(self):
        super(TestInvoice, self).setUp()
        # Proxies
        self.iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')

        self.document_book_proxy = self.env['document.book']
        self.pos_proxy = self.env['pos.ar']

        self._create_partners()
        self._create_invoices()
        self._create_invoice_lines()

        # Configuracion de posicion fiscal RI en la compania
        self.env.user.company_id.partner_id.property_account_position_id = self.iva_ri

    def test_invoice_no_taxes(self):
        self.invoice._onchange_invoice_line_ids()
        assert self.invoice.amount_total == self.invoice.amount_not_taxable
        assert self.invoice.amount_exempt == 0.0
        assert self.invoice.amount_to_tax == 0.0

    def test_invoice_with_vat(self):
        self._create_invoice_line_with_vat()
        self.invoice._onchange_invoice_line_ids()

        assert self.invoice.amount_not_taxable == 500
        assert self.invoice.amount_to_tax == 1000
        assert self.invoice.amount_exempt == 0.0
        assert self.invoice.amount_total == 1710

    def test_exempt_invoice(self):
        self._create_invoice_line_with_exempt_tax()
        self.invoice._onchange_invoice_line_ids()

        assert self.invoice.amount_not_taxable == 500
        assert self.invoice.amount_to_tax == 0.0
        assert self.invoice.amount_exempt == 1500
        assert self.invoice.amount_total == 2000

    def test_mixed_invoice(self):
        self._create_invoice_line_with_exempt_tax()
        self._create_invoice_line_with_vat()
        self.invoice._onchange_invoice_line_ids()

        assert self.invoice.amount_not_taxable == 500
        assert self.invoice.amount_to_tax == 1000
        assert self.invoice.amount_exempt == 1500
        assert self.invoice.amount_total == 3210

    def test_no_vat(self):
        tax_group_vat = self.env.ref('l10n_ar.tax_group_vat')

        # Desasignamos los impuestos creados al grupo de iva y luego borramos el grupo
        vat_taxes = self.env['account.tax'].search([('tax_group_id', '=', tax_group_vat.id)])
        vat_taxes.write({'tax_group_id': self.env['account.tax.group'].create({'name': 'test'}).id})
        tax_group_vat.unlink()

        with self.assertRaises(ValidationError):
            self.invoice._onchange_invoice_line_ids()

    def test_multiple_lines_with_vat(self):
        line = self._create_invoice_line_with_vat()
        vat_21 = self.env.ref('l10n_ar.1_vat_21_ventas').id
        vat_105 = self.env.ref('l10n_ar.1_vat_105_ventas').id
        line.invoice_line_tax_ids = [(6, 0, [vat_21, vat_105])]
        with self.assertRaises(ValidationError):
            self.invoice.check_more_than_one_vat_in_line()

    def test_amount_json(self):
        self._create_invoice_line_with_exempt_tax()
        self._create_invoice_line_with_vat()
        self.invoice._onchange_invoice_line_ids()

        amounts_widget = json.loads(self.invoice.amounts_widget)

        assert amounts_widget['content'][0].get('amount_to_tax') == 1000
        assert amounts_widget['content'][0].get('amount_not_taxable') == 500
        assert amounts_widget['content'][0].get('amount_exempt') == 1500

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
