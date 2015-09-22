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
from openerp.exceptions import except_orm

class account_bank_reconcile_line(models.Model):

    _name = "account.bank.reconcile.line"

    period_id = fields.Many2one('account.period', 'Period', readonly=True)
    last_balance = fields.Float('Last Balance', readonly=True)
    current_balance = fields.Float('Current Balance', readonly=True)
    move_line_ids = fields.One2many('account.move.line', 'bank_reconcile_line_id', 'Move lines', readonly=True)
    bank_reconcile_id = fields.Many2one('account.bank.reconcile', 'Bank reconcile', readonly=True, ondelete="cascade")


    ''' Redefinition of unlink method so the move lines are visible again'''
    @api.one
    def unlink(self):

        self.move_line_ids.write({'is_reconciled': False})

        reconcile_lines = self.search([('id', '>', self.id),('bank_reconcile_id','=',self.bank_reconcile_id.id)])

        if reconcile_lines:

            raise except_orm(_('Error!'), _('You cant delete a period that is not the higher!'))

        return super(account_bank_reconcile_line, self).unlink()

    _order = 'id desc'

account_bank_reconcile_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
