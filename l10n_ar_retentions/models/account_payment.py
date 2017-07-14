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

from openerp import models, fields, api


class AccountAbstractPayment(models.AbstractModel):

    _inherit = 'account.abstract.payment'

    retention_ids = fields.One2many(
        'account.payment.retention',
        'payment_id',
        'Retenciones'
    )

    @api.onchange('retention_ids')
    def onchange_retention_ids(self):
        self.recalculate_amount()

    def set_payment_methods_vals(self):

        vals = super(AccountAbstractPayment, self).set_payment_methods_vals()

        retentions = [
            {'amount': retention.amount, 'account_id': retention.retention_id.tax_id.account_id.id}
            for retention in self.retention_ids
        ]

        return vals+retentions

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
