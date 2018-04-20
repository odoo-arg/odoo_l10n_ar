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


class ResCurrencyRate(models.Model):

    _inherit = 'res.currency.rate'

    inverse_rate = fields.Float('Tasa inversa', digits=(12, 6))
    rate = fields.Float(digits=(12, 10))
    editable_inverse_rate = fields.Boolean(
        'Tasa inversa editable',
        related='currency_id.editable_inverse_rate'
    )

    @api.onchange('inverse_rate', 'rate')
    def onchange_rate(self):
        if self.editable_inverse_rate:
            self.rate = 1 / self.inverse_rate if self.inverse_rate else 0
        else:
            self.inverse_rate = 1 / self.rate if self.rate else 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
