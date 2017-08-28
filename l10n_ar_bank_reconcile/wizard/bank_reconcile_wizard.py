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

from openerp import models, fields
from openerp.exceptions import ValidationError


class BankReconcileWizard(models.TransientModel):
    _name = 'bank.reconcile.wizard'

    date_start = fields.Date(
        string='Fecha de inicio',
        required=True
    )
    date_stop = fields.Date(
        string='Fecha de fin',
        required=True
    )

    def create_conciliation(self):
        active_ids = self.env.context.get('active_ids')
        move_lines = self.env['account.move.line'].browse(active_ids)
        bank_reconciliation_obj = self.env['account.bank.reconcile']
        bank_reconcile_move_line_obj = self.env['account.reconcile.move.line']
        account_ids = []

        # Itero los movimientos y agrego las cuentas de los mismos
        for move_line in move_lines:
            if move_line.bank_reconciled:
                raise ValidationError('Ya existe una conciliacion para algun movimiento seleccionado.')
            if move_line.account_id.id not in account_ids:
                account_ids.append(move_line.account_id.id)
        if len(account_ids) != 1:
            raise ValidationError('Solo se puede crear conciliaciones para movimientos de la misma cuenta.')
        bank_reconciliation = bank_reconciliation_obj.search(
            [('account_id', '=', account_ids[0])]
        )
        if len(bank_reconciliation) < 1:
            raise ValidationError('No existe una conciliacion para la cuenta los movimientos seleccionados.')
        last_balance = 0
        if bank_reconciliation:
            # Suma del balance actual
            current_balance = sum(move_lines.debit - move_line.credit for move_line in move_lines)
            # Chequeo el rango de fechas
            self._check_date(self.date_start, self.date_stop, bank_reconciliation)
            flag_last = False
            # Obtengo el balance anterior
            if bank_reconciliation.bank_reconcile_line_ids:
                last_balance = bank_reconciliation.bank_reconcile_line_ids[0].current_balance
                flag_last = True
                if bank_reconciliation.bank_reconcile_line_ids[0].date_start < self.date_start\
                        < bank_reconciliation.bank_reconcile_line_ids[0].date_stop:
                    raise ValidationError('No se puede crear una conciliacion con fecha de inicio menor '
                                          'a la fecha de fin de la ultima conciliacion.')

            # Chequeo si existe una conciliacion que el rango de fechas seleccionado
            if flag_last and self.date_start >= bank_reconciliation.bank_reconcile_line_ids[0].date_start\
                    and bank_reconciliation.bank_reconcile_line_ids[0].date_stop >= self.date_stop:
                reconcile_line = bank_reconciliation.bank_reconcile_line_ids[0]
                reconcile_line.write({'current_balance': current_balance + last_balance})
                for move_line in move_lines:
                    bank_reconcile_move_line_obj.create({
                        'bank_reconcile_line_id': reconcile_line.id,
                        'move_line_id': move_line.id,
                    })
            else:
                if bank_reconciliation.bank_reconcile_line_ids:
                    bank_reconciliation.bank_reconcile_line_ids[0].last = False
                reconcile_line = bank_reconciliation.bank_reconcile_line_ids.create(
                    {'date_start': self.date_start,
                     'date_stop': self.date_stop,
                     'last_balance': last_balance,
                     'current_balance': current_balance + last_balance,
                     'bank_reconcile_id': bank_reconciliation.id,
                     'last': True}
                )
                for move_line in move_lines:
                    bank_reconcile_move_line_obj.create({
                        'bank_reconcile_line_id': reconcile_line.id,
                        'move_line_id': move_line.id,
                    })
            move_lines.write({'bank_reconciled': True})

    def _check_date(self, date_start, date_stop, bank_reconciliation):
        bank_reconcile_line_obj = self.env['account.bank.reconcile.line']
        if date_start > date_stop:
            raise ValidationError('Rango de fechas incorrecta.')
        # Busco si existen conciliaciones mayores que el rango seleccionado
        bank_reconcile_line = bank_reconcile_line_obj.search(
            [('date_stop', '>', date_stop),
             ('bank_reconcile_id', '=', bank_reconciliation.id)]
        )
        if bank_reconcile_line:
            raise ValidationError('Existe una conciliacion mas actual que el rango de fechas dado.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
