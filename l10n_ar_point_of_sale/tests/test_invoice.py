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
from openerp.exceptions import Warning

class TestInvoice(common.TransactionCase):

    def setUp(self):
        super(TestInvoice, self).setUp()

        partner = self.env['res.partner'].search([], limit=1)
        account = partner.property_account_receivable_id.id
        denomination = self.env['account.denomination'].search([], limit=1)
        pos_ar_id = self.env['pos.ar'].search([], limit=1)

        self.invoice = self.env['account.invoice'].create({
            'partner_id': partner.id,
            'fiscal_position_id': partner.property_account_position_id.id,
            'account_id': account.id,
            'denomination_id': denomination.id,
            'pos_ar_id': pos_ar_id.id
        })

        self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 1,
            'price_unit': 500,
            'invoice_id': self.invoice.id,
        })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: