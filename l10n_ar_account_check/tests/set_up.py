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
from openerp import fields


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

    def _create_payments(self):
        self.partner = self.env['res.partner'].create({
            'name': 'Partner',
            'supplier': True,
            'customer': True,
            'property_account_position_id': self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').id,
        })
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

    def _create_checks(self):
        third_check_proxy = self.env['account.third.check']
        date_today = fields.Date.context_today(third_check_proxy)
        self.third_check = self.env['account.third.check'].create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'amount': 1300,
            'currency_id': self.env.user.company_id.currency_id.id,
            'issue_date': date_today,
            'payment_date': date_today
        })

    def setUp(self):
        super(SetUp, self).setUp()
        self._create_payments()
        self._create_pos_data()
        self._create_checks()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
