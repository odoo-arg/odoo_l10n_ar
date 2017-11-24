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

from openerp import models, api

RETENTION_TYPE_CODES = {
    'profit': 'profit',
    'vat': 'vat',
    'gross_income': 'gross',
}


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post_l10n_ar(self):
        for rec in self.search([('partner_type', '=', 'supplier')]):
            for ret in rec.retention_ids.filtered(lambda x: not x.certificate_no):
                ret.certificate_no = self.env['ir.sequence'].next_by_code(
                    'rtl.{}.seq'.format(RETENTION_TYPE_CODES.get(ret.retention_id.type)))
        return super(AccountPayment, self).post_l10n_ar()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
