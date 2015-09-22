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

class account_bank_reconcile(models.Model):

    _name = "account.bank.reconcile"

    name = fields.Char('Name', required=True)
    account_id = fields.Many2one('account.account', 'Account', required=True)
    unreconciled_count = fields.Integer('Unreconciled elements', compute='_get_unreconciled_accounts')
    bank_reconcile_line_ids = fields.One2many('account.bank.reconcile.line', 'bank_reconcile_id', 'Conciliations', limit=12)

    _sql_constraints = [ ('field_unique', 'unique(account_id)', 'You are already using that account for a conciliation!')]

    #Search for all the unreconciled account move lines for this account
    @api.one
    def _get_unreconciled_accounts(self):

        self.unreconciled_count = self.env['account.move.line'].search_count([('is_reconciled', '=', False),
                                                                              ('account_id', '=', self.account_id.id)])

    @api.multi
    def open_unreconciled_accounts(self):

        return {

            'name': _('Bank statement to reconcile'),
            'views': [[False, "tree"]],
            'domain': [('account_id', '=', self.account_id.id), ('is_reconciled', '=', False)],
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
        }

    @api.one
    def unlink(self):

        if self.bank_reconcile_line_ids:

            raise except_orm(_('Error!'), _('You cant delete an account that already has conciliations, please delete the conciliations first'))

        return super(account_bank_reconcile, self).unlink()

account_bank_reconcile()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
