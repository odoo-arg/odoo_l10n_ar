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
from openerp.exceptions import ValidationError


class AccountPaymentTypeLine(models.Model):

    _name = 'account.payment.type.line'

    account_payment_type_id = fields.Many2one(
        'account.payment.type',
        'Linea de metodo de pago',
        required=True,
    )
    payment_id = fields.Many2one(
        'account.payment',
        'Pago',
        required=True,
        ondelete='cascade'
    )
    amount = fields.Monetary('Importe', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='account_payment_type_id.currency_id'
    )

    @api.constrains('amount')
    def constraint_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError('El importe de la linea de pago debe ser mayor a 0')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
