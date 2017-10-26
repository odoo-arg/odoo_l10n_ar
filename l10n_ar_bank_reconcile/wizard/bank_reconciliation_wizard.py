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


class bank_reconciliation_wizard(models.TransientModel):
    _name = 'bank.reconciliation.wizard'

    period_id = fields.Many2one('account.period', 'Period', required=True)
    bank_reconcile_id = fields.Many2one('account.account', 'Account')

    @api.one
    def create_conciliation(self):

        # Domain with the active account_id
        active_ids = self.env.context.get('active_ids')
        move_lines = self.env['account.move.line'].browse(active_ids)
        bank_reconciliation_obj = self.env['account.bank.reconcile']
        account_ids = []
        self._validate_conciliations(move_lines)
        for move_line in move_lines:
            if move_line.account_id.id not in account_ids:
                account_ids.append(move_line.account_id.id)
        bank_reconciliation = bank_reconciliation_obj.search([('account_id', '=', account_ids[0])])

        current_balance = 0
        current_balance_currency = 0
        last_balance = 0
        last_balance_currency = 0

        if bank_reconciliation:

            # Sum of the current_balance
            for move_line in move_lines:
                current_balance += move_line.debit - move_line.credit
                current_balance_currency += move_line.amount_currency

            # Check if the period is ok
            self._check_period(self.period_id, bank_reconciliation)

            flag_last = False

            # Get last balance
            if bank_reconciliation.bank_reconcile_line_ids:
                last_balance = bank_reconciliation.bank_reconcile_line_ids[0].current_balance
                last_balance_currency = bank_reconciliation.bank_reconcile_line_ids[0].current_balance_currency
                flag_last = True

            # Si habia un balance previo, chequeo si es el mismo que el seleccionado
            # Si? Agrego las move a ese balance.
            # No? Creo una nuevo linea de conciliacion.
            if flag_last and self.period_id.id == bank_reconciliation.bank_reconcile_line_ids[0].period_id.id:
                reconcile_line = bank_reconciliation.bank_reconcile_line_ids[0]
                reconcile_line.write({
                    'current_balance': current_balance + last_balance,
                    'current_balance_currency': current_balance_currency + last_balance_currency
                })
            else:
                if bank_reconciliation.bank_reconcile_line_ids:
                    bank_reconciliation.bank_reconcile_line_ids[0].last = False

                reconcile_line = bank_reconciliation.bank_reconcile_line_ids.create({
                    'period_id': self.period_id.id,
                    'last_balance': last_balance,
                    'last_balance_currency': last_balance_currency,
                    'current_balance': current_balance + last_balance,
                    'current_balance_currency': current_balance_currency + last_balance_currency,
                    'bank_reconcile_id': bank_reconciliation.id,
                    'last': True})

            move_lines.write({
                'is_reconciled': True,
                'bank_reconcile_line_id': reconcile_line.id
            })

    def _validate_conciliations(self, move_lines):
        account = move_lines.mapped('account_id')
        if len(account) != 1:
            raise except_orm('Error!', 'Solo se puede crear conciliaciones para movimientos de la misma cuenta.')

        currency = move_lines.mapped('currency_id')
        currency_account = account.currency_id if account.currency_id else account.company_id.currency_id
        if currency or account.currency_id:
            if len(currency) != 1 or currency != currency_account:
                raise except_orm('Error!', 'Solo se pueden conciliar movimientos de la misma moneda que la '
                                 'de la cuenta.')

    def _check_period(self, period, bank_reconciliation):
        """
        Checks if already exists a higher or equal period than the one of the concilation 
        """
        bank_reconcile_line_obj = self.env['account.bank.reconcile.line']
        account_period_obj = self.env['account.period']
        account_periods = account_period_obj.search([('date_start', '>', period.date_start)])
        bank_reconcile_line = bank_reconcile_line_obj.search([
            ('period_id', 'in', account_periods.ids),
            ('bank_reconcile_id', '=', bank_reconciliation.id)
        ])
        if bank_reconcile_line:
            raise except_orm(_('Error!'),
                             _('A period higher or equal than the one selected already exists for a concilation'))

bank_reconciliation_wizard()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
