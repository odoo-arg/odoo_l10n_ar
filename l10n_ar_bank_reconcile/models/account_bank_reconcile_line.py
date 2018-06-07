# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.exceptions import ValidationError


class AccountBankReconcileLine(models.Model):
    _name = 'account.bank.reconcile.line'
    _order = 'date_stop desc'

    date_start = fields.Date(
        string='Fecha de inicio',
        readonly=True,
    )
    date_stop = fields.Date(
        string='Fecha de fin',
        readonly=True,
    )
    last_balance = fields.Float(
        'Balance anterior',
    )
    current_balance = fields.Float(
        'Balance actual',
    )
    last_balance_currency = fields.Float(
        'Balance anterior en moneda'
    )
    current_balance_currency = fields.Float(
        'Balance actual en moneda'
    )
    reconcile_move_line_ids = fields.One2many(
        comodel_name='account.reconcile.move.line',
        inverse_name='bank_reconcile_line_id',
        string='Movimientos',
    )
    bank_reconcile_id = fields.Many2one(
        comodel_name='account.bank.reconcile',
        string='Conciliacion bancaria',
        readonly=True,
    )
    last = fields.Boolean(
        string='Ultimo',
    )

    company_id = fields.Many2one('res.company', string='Compania', related='bank_reconcile_id.company_id', store=True,
                                 readonly=True, related_sudo=False)

    @api.onchange('reconcile_move_line_ids')
    def onchange_balance(self):
        self.current_balance_currency = sum(
            line.amount_currency
            for line in self.reconcile_move_line_ids
        ) + self.last_balance_currency
        self.current_balance = sum(
            line.debit_move_line - line.credit_move_line
            for line in self.reconcile_move_line_ids
        ) + self.last_balance

    def unlink(self):
        if self.bank_reconcile_id.get_last_conciliation() != self:
            raise ValidationError('Solo se puede borrar la ultima conciliacion.')
        bank_reconcile = self.bank_reconcile_id
        self.reconcile_move_line_ids.unlink()
        res = super(AccountBankReconcileLine, self).unlink()
        if bank_reconcile.bank_reconcile_line_ids:
            bank_reconcile.get_last_conciliation().last = True
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
