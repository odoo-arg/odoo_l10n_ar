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
import time
from openerp.exceptions import Warning
from dateutil import parser
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)

class WizardAccountDepositSlip(models.TransientModel):

    _name = "wizard.account.deposit.slip"

    name = fields.Char(string='Boleta de deposito numero')
    date = fields.Date('Fecha', required=True)
    bank_account_id = fields.Many2one('res.partner.bank', 'Cuenta bancaria', required=True)
    company_id = fields.Many2one('res.company', 'Compania', required=True)
    journal_id = fields.Many2one('account.journal', 'Diario', domain=[('type','in',('cash', 'bank'))], required=True)

    _defaults = {

        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,

    }

    def _get_source_account_check(self, company_id):
        check_config_obj = self.env['account.check.config']

        res = check_config_obj.search([('company_id', '=', company_id)])

        if not res:
            raise Warning('No hay configuración de cheques para esta companía!')

        return res[0].account_id


    @api.multi
    def action_deposit(self):

        deposit_slip_obj = self.env['account.deposit.slip']
        third_check_obj = self.env['account.third.check']
        wf_service = netsvc.LocalService('workflow')
        move_line = self.env['account.move.line']
        period_id = self.env['account.period'].find(self.date)

        if period_id:

            period_id = period_id[0]

        deposit_date = self.date or time.strftime('%Y-%m-%d')

        if not self.bank_account_id.account_id:
            raise Warning("Configurar cuenta para la cuenta bancaria "+self.bank_account_id.bank_name+": "+self.bank_account_id.acc_number)

        active_ids = self.env.context.get('active_ids', [])
        company_id = self.company_id.id
        check_objs = third_check_obj.browse(active_ids)

        deposit_slip_amount = 0
        checks = []

        for check in check_objs:

            if check.state != 'wallet':
                raise Warning("Los cheques seleccionados deben estar en cartera. \n El cheque "+check.number +" no esta en cartera", )

            if check.payment_date > deposit_date:
                raise Warning("No se puede depositar el cheque " +check.number+ " la fecha del cheque es mayor que la de la boleta.", )

            account_check_id = self._get_source_account_check(company_id)

            deposit_slip_amount += check.amount

            check_vals = {'deposit_bank_id': self.bank_account_id.id, 'deposit_date': deposit_date}
            check.write(check_vals)

            wf_service.trg_validate(self.env.uid, 'account.third.check', check.id, 'cartera_deposited', self.env.cr)

            checks.append(check.id)

        sequence = self.env['ir.sequence'].get('account.deposit.slip.sequence')

        move_id = self.env['account.move'].create( {
            'name': sequence,
            'journal_id': self.journal_id.id,
            'state': 'draft',
            'period_id': period_id.id,
            'date': deposit_date,
            'ref': _('Deposit Slip Number %s') % sequence,
        })

        deposit_slip_obj.create({
            'name': sequence,
            'date': self.date,
            'bank_account_id': self.bank_account_id.id,
            'move_id': move_id.id,
            'total_amount': deposit_slip_amount,
            'checks_ids': [(6, 0, checks)],
            'state': 'deposited',
        })

        move_line.create({
            'name': sequence,
            'centralisation': 'normal',
            'account_id': self.bank_account_id.account_id.id,
            'move_id': move_id.id,
            'journal_id': self.journal_id.id,
            'period_id': period_id.id,
            'date': deposit_date,
            'debit': deposit_slip_amount,
            'credit': 0.0,
            'ref': _('Deposit Slip Number %s') % sequence,
            'state': 'valid',
        })

        move_line.create({
            'name': sequence,
            'centralisation': 'normal',
            'account_id': account_check_id.id,
            'move_id': move_id.id,
            'journal_id': self.journal_id.id,
            'period_id': period_id.id,
            'date': deposit_date,
            'debit': 0.0,
            'credit': deposit_slip_amount,
            'ref': _('Deposit Slip Number %s') % sequence,
            'state': 'valid',
        })

        move_id.post()

        return { 'type': 'ir.actions.act_window_close' }

WizardAccountDepositSlip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
