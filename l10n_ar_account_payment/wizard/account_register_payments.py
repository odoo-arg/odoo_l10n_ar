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


class AccountRegisterPaymnets(models.TransientModel):

    _inherit = 'account.register.payments'

    def get_payment_vals(self):

        res = super(AccountRegisterPaymnets, self).get_payment_vals()

        res['pos_ar_id'] = self.pos_ar_id.id
        res['payment_type_line_ids'] = [(4, payment) for payment in self.payment_type_line_ids.ids]

        return res

    @api.multi
    def create_payment_l10n_ar(self):
        payment = self.env['account.payment'].create(self.get_payment_vals())
        payment.post_l10n_ar()
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
