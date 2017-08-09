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

from openerp.tests import common


class TestInvoice(common.TransactionCase):

    def _create_partners(self):
        self.partner_ri = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
            'supplier': True,
            'property_account_position_id': self.iva_ri.id
        })
        self.partner_cf = self.env['res.partner'].create({
            'name': 'Supplier',
            'customer': True,
            'supplier': True,
            'property_account_position_id': self.iva_cf.id
        })

    def _create_invoices(self):
        account = self.partner_ri.property_account_receivable_id
        self.pos = self.env['pos.ar'].create({'name': 5})
        self.document_book = self.env['document.book'].create({
            'name': 15,
            'pos_ar_id': self.pos.id,
            'category': 'invoice',
            'book_type_id': self.env.ref('l10n_ar_point_of_sale.document_book_type_preprint_invoice').id,
            'document_type_id': self.env.ref('l10n_ar_debit_note.document_type_debit_note').id,
            'denomination_id': self.env.ref('l10n_ar_afip_tables.account_denomination_a').id,
        })
        self.debit_note = self.env['account.invoice'].create({
            'partner_id': self.partner_ri.id,
            'fiscal_position_id': self.partner_ri.property_account_position_id.id,
            'account_id': account.id,
            'type': 'out_invoice',
            'state': 'draft',
            'is_debit_note': True,
        })
        self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 1,
            'price_unit': 500,
            'invoice_id': self.debit_note.id,
        })

    def setUp(self):
        super(TestInvoice, self).setUp()
        self.iva_ri = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        self.iva_cf = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_cf')
        self.env.user.company_id.partner_id.property_account_position_id = self.iva_ri
        self.company_fiscal_position = self.env.user.company_id.partner_id.property_account_position_id
        # Clientes y proveedores
        self._create_partners()

        # Documentos
        self._create_invoices()

    def test_name_get_customer(self):
        assert self.debit_note.name_get()[0][1] == 'NDC'
        # El onchange nos deberia dar la denominacion
        self.debit_note.onchange_partner_id()
        assert self.debit_note.name_get()[0][1] == 'NDC A'
        # Al validarla deberia darnos la numeracion del talonario
        self.debit_note.action_invoice_open()
        pos_ar_name_get = self.pos.name_get()[0][1]
        document_book_name_get = self.document_book.name_get()[0][1]
        assert self.debit_note.name_get()[0][1] == 'NDC A '+pos_ar_name_get+'-'+document_book_name_get

    def test_name_get_supplier(self):
        self.debit_note.type = 'in_invoice'
        assert self.debit_note.name_get()[0][1] == 'NDP'
        self.partner_ri.property_account_position_id = self.iva_cf.id
        self.debit_note.onchange_partner_id()
        self.debit_note._onchange_partner_id()
        # El onchange nos deberia dar la denominacion
        assert self.debit_note.name_get()[0][1] == 'NDP C'
        self.debit_note.name = '5-3'
        self.debit_note.action_invoice_open()
        assert self.debit_note.name_get()[0][1] == 'NDP C 0005-00000003'

    def test_name_get_non_debit_note(self):
        """ Nos aseguramos de que siga funcionando el name get anterior """
        self.debit_note.type = 'out_refund'
        self.debit_note.is_debit_note = False
        assert self.debit_note.name_get()[0][1] == 'NCC'

    def test_check_invoice_duplicity(self):
        self.debit_note.onchange_partner_id()
        self.debit_note.check_invoice_duplicity()

    def test_get_document_book(self):
        self.debit_note.onchange_partner_id()
        self.debit_note.get_document_book()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
