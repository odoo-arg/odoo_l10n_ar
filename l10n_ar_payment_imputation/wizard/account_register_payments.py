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


class AccountRegisterPayments(models.TransientModel):

    _inherit = 'account.register.payments'

    payment_imputation_ids = fields.Many2many(
        'payment.imputation.line',
        'imputation_payment_rel',
        'payment_id',
        'imputation_id',
        'Imputaciones',
    )

    def get_payment_vals(self):

        res = super(AccountRegisterPayments, self).get_payment_vals()
        res['payment_imputation_ids'] = [(4, imputation) for imputation in self.payment_imputation_ids.ids]

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
