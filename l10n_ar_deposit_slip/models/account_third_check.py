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


class AccountThirdCheck(models.Model):

    _inherit = 'account.third.check'

    deposit_slip_id = fields.Many2one(
        'account.deposit.slip',
        'Boleta de deposito',
        readonly=True
    )
    deposit_bank_id = fields.Many2one(
        'account.journal',
        'Cuenta de deposito',
        related='deposit_slip_id.journal_id',
        readonly=True
    )
    deposit_date = fields.Date(
        'Fecha de deposito',
        related='deposit_slip_id.date',
        readonly=True
    )

    @api.constrains('deposit_slip_id')
    def check_state_on_deposit_slip_assignation(self):
        if any(check.state != 'wallet' for check in self):
            raise ValidationError('Solo se puede modificar la boleta de deposito de un cheque en cartera.')

    @api.multi
    def post_deposit_slip(self):
        if any(check.state != 'wallet' for check in self):
            raise ValidationError("Todos los cheques a depositar deben estar en cartera")
        if len(self.mapped('currency_id')) > 1:
            raise ValidationError("No se pueden depositar cheques de distintas monedas en la misma boleta de deposito")
        self.next_state('wallet_deposited')

    @api.multi
    def cancel_deposit_slip(self):
        if any(check.state != 'deposited' for check in self):
            raise ValidationError("Para cancelar la boleta de deposito todos los cheques deben estar depositados")
        self.cancel_state('deposited')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
