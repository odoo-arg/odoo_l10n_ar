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


import calendar
import assert_details
from openerp import fields
from openerp.exceptions import ValidationError
from openerp.fields import date
from odoo.tests import common


class TestVatDiary(common.TransactionCase):

    def _create_partners(self):
        vals = {
            'customer': True,
            'supplier': True,
            'name': 'Partner',
            'state_id': self.env.ref('base.state_ar_b').id,
            'property_account_position_id': self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id,
            'vat': '30000000003'
        }

        self.partner_ri = self.env['res.partner'].create(vals.copy())
        vals['property_account_position_id'] = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_cf').id
        self.partner_cf = self.env['res.partner'].create(vals.copy())

    def _create_invoices(self):
        account = self.partner_ri.property_account_receivable_id
        invoice_vals = {
            'partner_id': self.partner_ri.id,
            'fiscal_position_id': self.partner_ri.property_account_position_id.id,
            'account_id': account.id,
            'type': 'out_invoice',
            'state': 'draft'
        }

        self.invoice = self.env['account.invoice'].create(invoice_vals.copy())
        invoice_vals['type'] = 'out_refund'
        self.refund = self.env['account.invoice'].create(invoice_vals.copy())
        invoice_vals['type'] = 'out_invoice'
        invoice_vals['is_debit_note'] = True
        self.debit_note = self.env['account.invoice'].create(invoice_vals.copy())
        invoice_line_vals = {
            'name': 'Producto',
            'account_id': self.env.ref('l10n_ar.1_bienes_de_cambio').id,
            'quantity': 1,
            'price_unit': 500,
            'invoice_id': self.invoice.id,
            'invoice_line_tax_ids': [(6, 0, [
                self.env.ref('l10n_ar.1_vat_21_ventas').id, self.env.ref('l10n_ar.1_vat_enard').id
            ])]
        }
        self.env['account.invoice.line'].create(invoice_line_vals.copy())
        invoice_line_vals['invoice_id'] = self.refund.id,
        invoice_line_vals['invoice_line_tax_ids'] = [(6, 0, [self.env.ref('l10n_ar.1_vat_105_ventas').id])]
        self.env['account.invoice.line'].create(invoice_line_vals.copy())
        invoice_line_vals['invoice_id'] = self.debit_note.id
        invoice_line_vals['invoice_line_tax_ids'] = [(6, 0, [self.env.ref('l10n_ar.1_vat_enard').id])]
        self.env['account.invoice.line'].create(invoice_line_vals.copy())
        self.invoices = self.invoice | self.refund | self.debit_note

    def _create_document_books(self):
        self.pos = self.env['pos.ar'].create({'name': 5})
        document_book_proxy = self.env['document.book']
        self.document_book = document_book_proxy.create({
            'name': 32,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })
        self.document_book_debit = document_book_proxy.create({
            'name': 15,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_debit_note').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })
        self.document_book_refund = document_book_proxy.create({
            'name': 32,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_refund').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })

    def _validate_invoices(self):
        for invoice in self.invoices:
            invoice.onchange_partner_id()
            invoice._onchange_invoice_line_ids()
            invoice.action_invoice_open()

    def setUp(self):
        super(TestVatDiary, self).setUp()
        # Configuracion de posicion fiscal RI en la compania
        self.env.user.company_id.partner_id.property_account_position_id = \
            self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id

        self._create_document_books()
        self._create_partners()
        self._create_invoices()
        self.tax_subdiary_wizard = self.env['wizard.vat.diary'].create({
            'type': 'sales',
            'date_from': fields.Date.to_string(date.today().replace(day=1)),
            'date_to': fields.Date.to_string(
                date.today().replace(day=calendar.monthrange(date.today().year, date.today().month)[1])
            )
        })

    def test_get_taxes_position(self):
        self._validate_invoices()
        taxes_position = self.tax_subdiary_wizard._get_taxes_position(self.invoices)
        # Deberiamos tener 2 iva, un Enard ya que se deberia eliminar el Enard duplicado
        assert len(taxes_position) == 3
        # El iva deberia estar primero y por ultimo el enard
        assert taxes_position.get(self.env.ref('l10n_ar.1_vat_105_ventas')) == 0
        assert taxes_position.get(self.env.ref('l10n_ar.1_vat_21_ventas')) == 2
        assert taxes_position.get(self.env.ref('l10n_ar.1_vat_enard')) == 4

    def test_get_header_values(self):
        self._validate_invoices()
        taxes_position = self.tax_subdiary_wizard._get_taxes_position(self.invoices)
        header = self.tax_subdiary_wizard.get_header_values(taxes_position)
        assert_details._assert_header_values(self, header)

    def test_get_details_values_customer(self):
        self.invoice.date_invoice = fields.Date.to_string(date.today().replace(day=1))
        self.refund.date_invoice = fields.Date.to_string(date.today().replace(day=2))
        self.debit_note.date_invoice = fields.Date.to_string(date.today().replace(day=3))
        self._validate_invoices()
        taxes_position = self.tax_subdiary_wizard._get_taxes_position(self.invoices)
        details = self.tax_subdiary_wizard.get_details_values(taxes_position, self.invoices)
        assert_details._assert_invoices_values_customer(self, details)

    def test_get_details_values_supplier(self):
        self.invoice.write({
            'name': '0001-00000111',
            'date_invoice': fields.Date.to_string(date.today().replace(day=1)),
            'type': 'in_invoice'
        })
        self.refund.write({
            'name': '0001-00000111',
            'date_invoice': fields.Date.to_string(date.today().replace(day=2)),
            'type': 'in_refund'
        })
        self.debit_note.write({
            'name': '0001-00000111',
            'date_invoice': fields.Date.to_string(date.today().replace(day=3)),
            'type': 'in_invoice'
        })
        self._validate_invoices()
        taxes_position = self.tax_subdiary_wizard._get_taxes_position(self.invoices)
        details = self.tax_subdiary_wizard.get_details_values(taxes_position, self.invoices)
        assert_details._assert_invoices_values_supplier(self, details)

    def test_invoices_not_found(self):
        self.tax_subdiary_wizard.write({
            'date_from': fields.Date.to_string(date.today().replace(day=20)),
            'date_to': fields.Date.to_string(date.today().replace(day=20))
        })
        with self.assertRaises(ValidationError):
            self.tax_subdiary_wizard._get_invoices()

    def test_invalid_date_range(self):
        with self.assertRaises(ValidationError):
            self.tax_subdiary_wizard.write({
                'date_from': fields.Date.to_string(date.today().replace(day=10)),
                'date_to': fields.Date.to_string(date.today().replace(day=5))
            })

    def test_report_generation_xls(self):
        self._validate_invoices()
        self.tax_subdiary_wizard.generate_xls_report()
        self.invoices.write({'type': 'in_invoice'})
        self.tax_subdiary_wizard.type = 'purchases'
        self.tax_subdiary_wizard.generate_xls_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
