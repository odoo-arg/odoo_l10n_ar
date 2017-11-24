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
        bank_reconcile_move_line_obj = self.env['account.reconcile.move.line']

        # Validamos las move lines y fechas de la conciliacion
        bank_reconciliation = self._validate_conciliation(move_lines)

        last_balance = 0
        last_balance_currency = 0
        # Suma del balance actual
        current_balance = sum(move_line.debit - move_line.credit for move_line in move_lines)
        current_balance_currency = sum(move_line.amount_currency for move_line in move_lines)

        reconcile_lines = bank_reconciliation.bank_reconcile_line_ids

        # Obtengo el balance anterior
        if reconcile_lines:
            last_balance, last_balance_currency = [reconcile_lines[0].current_balance,
                                                   reconcile_lines[0].current_balance_currency]
            if reconcile_lines[0].date_start < self.date_start < reconcile_lines[0].date_stop:
                raise ValidationError(
                    'No se puede crear una conciliacion con fecha de inicio menor '
                    'a la fecha de fin de la ultima conciliacion.'
                )

        # Chequeo si existe una conciliacion con el rango de fechas seleccionado, en ese caso actualizamos los valores
        if reconcile_lines and self.date_start == reconcile_lines[0].date_start \
                and reconcile_lines[0].date_stop == self.date_stop:
            reconcile_line = reconcile_lines[0]
            reconcile_line.write({
                'current_balance': current_balance + last_balance,
                'current_balance_currency': current_balance_currency + last_balance_currency
            })
            for move_line in move_lines:
                bank_reconcile_move_line_obj.create({
                    'bank_reconcile_line_id': reconcile_line.id,
                    'move_line_id': move_line.id,
                })
        # Caso contrario creamos una conciliacion nueva
        else:
            if reconcile_lines:
                reconcile_lines[0].last = False
            reconcile_line = bank_reconciliation.bank_reconcile_line_ids.create({
                'date_start': self.date_start,
                'date_stop': self.date_stop,
                'last_balance': last_balance,
                'current_balance': current_balance + last_balance,
                'last_balance_currency': last_balance_currency,
                'current_balance_currency': current_balance_currency + last_balance_currency,
                'bank_reconcile_id': bank_reconciliation.id,
                'last': True
            })
            for move_line in move_lines:
                bank_reconcile_move_line_obj.create({
                    'bank_reconcile_line_id': reconcile_line.id,
                    'move_line_id': move_line.id,
                })
        move_lines.write({'bank_reconciled': True})

    def _validate_conciliation(self, move_lines):
        """
        Valida que no se pueda realizar una conciliacion incorrecta
        :param move_lines: Move lines seleccionadas para la conciliacion
        :raises ValidationError: - Ya existe una conciliacion en la linea que se quiere conciliar
                                 - Se seleccionan movimientos de distintas cuentas
                                 - No existe una conciliacion creada para la cuenta de las lineas
                                 - Las fechas seleccionadas son incorrectas
                                 - Existe una conciliacion con fecha mayor a la seleccionada
        :return: Conciliacion bancaria de la cuenta de los move lines
        """
        if any(move_lines.mapped('bank_reconciled')):
            raise ValidationError('Ya existe una conciliacion para algun movimiento seleccionado.')
        account = move_lines.mapped('account_id')
        if len(account) != 1:
            raise ValidationError('Solo se puede crear conciliaciones para movimientos de la misma cuenta.')
        currency = move_lines.mapped('currency_id')
        currency_account = account.currency_id if account.currency_id else account.company_id.currency_id
        if currency or account.currency_id:
            if len(currency) != 1 or currency != currency_account:
                raise ValidationError('Solo se pueden conciliar movimientos de la misma moneda que la '
                                      'de la cuenta.')
        bank_reconciliation = self.env['account.bank.reconcile'].search([('account_id', '=', account.id)])
        if not bank_reconciliation:
            raise ValidationError('No existe una conciliacion para la cuenta los movimientos seleccionados.')

        bank_reconcile_line_obj = self.env['account.bank.reconcile.line']
        if self.date_start > self.date_stop:
            raise ValidationError('Rango de fechas incorrecta.')

        # Busco si existen conciliaciones mayores que el rango seleccionado
        bank_reconcile_line = bank_reconcile_line_obj.search(
            [('date_stop', '>', self.date_stop),
             ('bank_reconcile_id', '=', bank_reconciliation.id)]
        )
        if bank_reconcile_line:
            raise ValidationError('Ya existe una conciliacion con fecha fin mayor a la seleccionada')

        return bank_reconciliation

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
