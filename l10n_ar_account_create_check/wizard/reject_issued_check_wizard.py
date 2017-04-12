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

from openerp import models, fields, api
from datetime import date
import logging
_logger = logging.getLogger(__name__)

class CancelIssuedCheckWizard(models.TransientModel):

    _name = "reject.issued.check.wizard"

    def _get_debit_account_id(self):
            
        active_ids = self.env.context.get('active_ids')
        
        for check in self.env['account.issued.check'].browse(active_ids):
            
            return check.account_id.id
        
    date = fields.Date('Fecha', default=date.today(), required=True)
    debit_account_id = fields.Many2one('account.account', 'Cuenta debe', default=_get_debit_account_id, required=True)
    credit_account_id = fields.Many2one('account.account', 'Cuenta haber', required=True)
    journal_id = fields.Many2one('account.journal', 'Diario', required=True)
    
    @api.one
    def reject_check(self):

        active_ids = self.env.context.get('active_ids')
        move_line_proxy = self.env['account.move.line']
        period = self.env['account.period'].find(self.date)
        
        for check in self.env['account.issued.check'].browse(active_ids):
            
            ref = 'Rechazo de cheque propio '+  check.number
            
            move = self.env['account.move'].create({
                'journal_id': self.journal_id.id,
                'state': 'draft',
                'period_id': period.id,
                'date': self.date,
                'ref': ref,
                })
                    
            move_line_proxy.create({
                'name': ref,
                'account_id': self.credit_account_id.id,
                'move_id': move.id,
                'journal_id': self.journal_id.id,
                'period_id': period.id,
                'date': self.date,
                'debit': 0.0,
                'credit': check.amount,
                'ref': ref,
                'state': 'valid',
            })

            move_line_proxy.create({
                'name': ref,
                'account_id': self.debit_account_id.id,
                'move_id': move.id,
                'journal_id': self.journal_id.id,
                'period_id': period.id,
                'date': self.date,
                'debit': check.amount,
                'credit': 0.0,
                'ref': ref,
                'state': 'valid',
            })
            
            check.rejected = True
            check.reject_move_id = move.id
            move.post()
        
CancelIssuedCheckWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
