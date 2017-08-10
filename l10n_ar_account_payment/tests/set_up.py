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

    def _create_pos_data(self):
        self.pos_inbound = self.env['pos.ar'].create({
            'name': '1'
        })
        self.pos_outbound = self.env['pos.ar'].create({
            'name': '10'
        })
        self.document_book_inbound = self.env['document.book'].with_context(default_payment_type='inbound').create({
            'name': '1',
            'category': 'payment',
            'pos_ar_id': self.pos_inbound.id,
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_payment').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_inbound').id
        })
        self.document_book_outbound = self.env['document.book'].create({
            'name': '5',
            'category': 'payment',
            'pos_ar_id': self.pos_outbound.id,
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_payment').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_outbound').id
        })
        self.document_book_invoice = self.env['document.book'].create({
            'name': '1',
            'category': 'invoice',
            'pos_ar_id': self.pos_inbound.id,
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_point_of_sale.document_type_invoice').id,
            'denomination_id': self.env.ref('l10n_ar_point_of_sale.account_denomination_a').id
        })

    def _create_payment_methods(self):
        self.payment_type_transfer = self.env['account.payment.type'].create({
            'name': 'Transferencia',
            'account_id': self.env.ref('l10n_ar.1_banco').id,
        })

    def _create_invoices(self):
        invoice_proxy = self.env['account.invoice']
        invoice_line_proxy = self.env['account.invoice.line']
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
        super(SetUp, self).setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'supplier': True,
            'customer': True,
            'property_account_position_id': self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id,
        })
        self._create_pos_data()
        self._create_payment_methods()
        self._create_invoices()
        self.customer_payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'amount': 500
        })
        self.supplier_payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
            'amount': 500
        })
        self.payment_line = self.env['account.payment.type.line'].create({
            'account_payment_type_id': self.payment_type_transfer.id,
            'payment_id': self.customer_payment.id,
            'amount': 500
        })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
