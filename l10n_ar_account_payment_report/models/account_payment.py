# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def _get_partial_ids(self):
        move_line_proxy = self.env['account.move.line']
        # Para clientes
        if self.payment_type == 'inbound':
            move_lines = move_line_proxy.search([('payment_id', '=', self.ids)])
            for line in move_lines:
                if line.credit > 0:
                    return line.matched_debit_ids
        # Para proveedor
        if self.payment_type == 'outbound':
            move_lines = move_line_proxy.search([('payment_id', '=', self.ids)])
            for line in move_lines:
                if line.debit > 0:
                    return line.matched_credit_ids

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
