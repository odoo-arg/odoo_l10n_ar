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


class AccountPaymentType(models.Model):

    _name = 'account.payment.type'

    name = fields.Char('Nombre', required=True)
    account_id = fields.Many2one(
        'account.account',
        'Cuenta',
        domain=[('deprecated', '=', False)],
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Compania',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Moneda',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
