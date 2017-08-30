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


class SetUp(common.TransactionCase):
    """
    La idea es crear distintos tipos de documentos y combinaciones para ser usado en las funciones posteriormente y
    para otros modulos de facturacion
    """

    def _set_up_company(self):
        company = self.env.user.company_id
        company.partner_id.property_account_position_id = \
            self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id
        self.company_fiscal_position = company.partner_id.property_account_position_id
        company.partner_id.vat = '33693450239'

    def _create_document_books(self):
        pos_proxy = self.env['pos.ar']
        document_book_proxy = self.env['document.book']
        self.pos = pos_proxy.create({
            'name': '0010'
        })
        vals = {
            'name': '0',
            'category': 'invoice',
            'pos_ar_id': self.pos.id,
            'book_type_id': self.env.ref('l10n_ar_afip_webservices_wsfe.document_book_type_electronic_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id
        }
        self.document_book_fc_a = document_book_proxy.create(vals)
        vals['document_type_id'] = self.env.ref('l10n_ar_point_of_sale.document_type_refund').id
        vals['denomination_id'] = self.env.ref('l10n_ar_afip_tables.account_denomination_b').id
        self.document_book_nc_b = document_book_proxy.create(vals)
        vals['document_type_id'] = self.env.ref('l10n_ar_point_of_sale.document_type_debit_note').id
        vals['denomination_id'] = self.env.ref('l10n_ar_afip_tables.account_denomination_c').id
        self.document_book_nd_c = document_book_proxy.create(vals)

    def _create_partners(self):
        self.partner_cuit = self.env['res.partner'].create({
            'name': 'Test',
            'supplier': True,
            'customer': True,
            'partner_document_type_id': self.env.ref('l10n_ar_afip_tables.partner_document_type_80').id,
            'country_id': self.env.ref('base.ar').id,
            'property_account_position_id': self.company_fiscal_position.id
        })
        cf = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_cf')
        self.partner_dni = self.env['res.partner'].create({
            'name': 'Test',
            'supplier': True,
            'customer': True,
            'partner_document_type_id': self.env.ref('l10n_ar_afip_tables.partner_document_type_96').id,
            'property_account_position_id': cf.id

        })
        mon = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_mon')
        self.partner_cuil = self.env['res.partner'].create({
            'name': 'Test',
            'supplier': True,
            'customer': True,
            'partner_document_type_id': self.env.ref('l10n_ar_afip_tables.partner_document_type_86').id,
            'property_account_position_id': mon.id
        })

    def _create_products(self):
        self.product_21_consu = self.env['product.product'].create({
            'name': '21 consu',
            'type': 'consu',
            'taxes_id': [(6, 0, [self.env.ref('l10n_ar.1_vat_21_ventas').id])]
        })
        self.product_105_serv = self.env['product.product'].create({
            'name': '105 service',
            'type': 'service',
            'taxes_id': [(6, 0, [self.env.ref('l10n_ar.1_vat_105_ventas').id])]
        })

    def _create_debit_note_c(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        self.debit_note = invoice_proxy.create({
            'partner_id': self.partner_cuil.id,
            'type': 'out_invoice',
            'is_debit_note': True
        })
        mon = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_mon')
        self.env.user.company_id.partner_id.property_account_position_id = mon.id
        self.debit_note.onchange_partner_id()
        invoice_line = invoice_line_proxy.create({
            'name': 'Exent',
            'price_unit': 5000,
            'account_id': self.product_105_serv.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.debit_note.id,
            'invoice_line_tax_ids': [(6, 0, [self.env.ref('l10n_ar.1_vat_exento_ventas').id])]
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 5000
        self.debit_note._onchange_invoice_line_ids()
        self.env.user.company_id.partner_id.property_account_position_id = \
            self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id

    def _create_refund_b(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        self.refund = invoice_proxy.create({
            'partner_id': self.partner_dni.id,
            'type': 'out_refund'
        })
        self.refund.onchange_partner_id()
        invoice_line = invoice_line_proxy.create({
            'name': 'product_105_test',
            'product_id': self.product_105_serv.id,
            'price_unit': 0,
            'account_id': self.product_105_serv.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.refund.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 2500
        invoice_line = invoice_line_proxy.create({
            'name': 'no_tax',
            'price_unit': 150,
            'account_id': self.product_105_serv.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.refund.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 150
        self.refund._onchange_invoice_line_ids()

    def _create_invoice_a(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
        self.invoice = invoice_proxy.create({
            'partner_id': self.partner_cuit.id,
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

    def _create_invoices(self):
        self._create_invoice_a()
        self._create_refund_b()
        self._create_debit_note_c()

    def setUp(self):
        super(SetUp, self).setUp()
        self._set_up_company()
        self._create_document_books()
        self._create_partners()
        self._create_products()
        self._create_invoices()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
