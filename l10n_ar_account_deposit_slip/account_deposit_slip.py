# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from dateutil import parser
from openerp import netsvc

class AccountDepositSlip(models.Model):

    _name = "account.deposit.slip"

    _description = 'Deposit slip'

    name = fields.Char(string='Numero boleta de deposito',size=128, select=True, required=True, readonly=True, ondelete='set null')
    date = fields.Date('Fecha boleta de deposito',readonly=True)
    bank_account_id = fields.Many2one('res.partner.bank', 'Cuenta Bancaria',required=True)
    total_ammount = fields.Float('Importe total',readonly=True)
    checks_ids = fields.One2many('account.third.check','deposit_slip_id',string='Cheques', readonly=True)
    state = fields.Selection([('canceled', 'Cancelado'), ('deposited', 'Depositado')], string='Estado')
    move_id = fields.Many2one('account.move', 'Asiento contable', readonly=True)

    _sql_constraints = [('name_uniq','unique(name)','The name must be unique!')]

    _order = "date desc, name desc"

    @api.one
    def cancel_deposit_slip(self):

        if not self.move_id:

            raise Warning('No hay un asiento relacionado a la boleta de depósito')

        reconcile_pool = self.env['account.move.reconcile']

        self.move_id.button_cancel()
        self.move_id.unlink()

        wf_service = netsvc.LocalService('workflow')

        for check in self.checks_ids:

            if check.state != 'deposited':

                raise Warning('El cheque '+check.number+' no se encuentra en estado depositado')

            wf_service.trg_validate(self.env.uid, 'account.third.check', check.id, 'deposited_cartera', self.env.cr)

        self.state = 'canceled'

AccountDepositSlip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
