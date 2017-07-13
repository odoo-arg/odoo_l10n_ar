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

from openerp import models, fields


class AccountRegisterPaymnets(models.TransientModel):

    _inherit = 'account.register.payments'

    # Cheques recibidos
    account_third_check_ids = fields.Many2many(
        'account.third.check',
        'third_check_wizard_payment_rel',
        'source_payment_id',
        'third_check_id',
        'Cheques de terceros'
    )
    # Cheques entregados
    account_third_check_sent_ids = fields.Many2many(
        'account.third.check',
        'sent_third_check_wizard_payment_rel',
        'destination_payment_id',
        'third_check_id',
        'Cheques de terceros'
    )
    account_own_check_line_ids = fields.Many2many(
        'account.own.check.line',
        'own_check_wizard_payment_rel',
        'payment_id',
        'own_check_id',
        'Cheques propios'
    )

    def get_payment_vals(self):

        res = super(AccountRegisterPaymnets, self).get_payment_vals()

        res['account_third_check_ids'] = [(4, payment) for payment in self.account_third_check_ids.ids]
        res['account_third_check_sent_ids'] = [(4, payment) for payment in self.account_third_check_sent_ids.ids]
        res['account_own_check_line_ids'] = [(4, payment) for payment in self.account_own_check_line_ids.ids]

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
