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

from openerp import models, fields
from openerp.exceptions import ValidationError


class WizardDepositSlip(models.TransientModel):

    _name = "wizard.deposit.slip"

    def get_total(self):
        checks = self.env['account.third.check'].browse(self.env.context.get('active_ids', []))
        return sum(check.amount for check in checks)

    def get_currency(self):
        checks = self.env['account.third.check'].browse(self.env.context.get('active_ids', []))
        if checks:
            currency = checks.mapped('currency_id')
            if len(currency) > 1:
                raise ValidationError("No se pueden depositar cheques de distintas monedas"
                                      " en la misma boleta de deposito")
            return currency.id

    journal_id = fields.Many2one(
        'account.journal',
        'Cuenta bancaria',
        domain=[('type', '=', 'bank')],
        required=True
    )
    date = fields.Date(
        'Fecha',
        default=fields.Date.context_today,
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Moneda',
        required=True,
        default=get_currency
    )
    total = fields.Monetary(
        'Total',
        default=get_total
    )

    def action_deposit(self):
        """
        Deposita los cheques y crea la boleta de deposito relacionada
        :return: Formulario de la boleta de deposito creada
        """

        name = self.env['ir.sequence'].next_by_code('account.deposit.slip.sequence')
        move = self._create_move(name)
        deposit_slip = self._create_deposit_slip(name, move)

        return {
            'name': 'Boleta de deposito',
            'views': [[False, "form"]],
            'res_model': 'account.deposit.slip',
            'type': 'ir.actions.act_window',
            'res_id': deposit_slip.id,
        }

    def _create_deposit_slip(self, name, move):
        """
        Crea la boleta de deposito y la asocia al asiento
        :param name: Nombre de de la boleta de deposito
        :param move: Asiento asociado a la boleta de deposito
        :return: account.deposit.slip - Boleta de deposito creada
        """

        checks = self.env['account.third.check'].browse(self.env.context.get('active_ids'))
        checks.post_deposit_slip()

        deposit_slip = self.env['account.deposit.slip'].create({
            'name': name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'move_id': move.id,
            'amount': self.total,
            'checks_ids': [(6, 0, checks.ids)],
            'state': 'deposited',
            'currency_id': self.currency_id.id
        })

        return deposit_slip

    def _create_move(self, name):
        """
        Crea el asiento de la boleta de deposito
        :param name: Nombre del asiento
        :return: account.move creado
        """

        vals = {
            'name': name,
            'date': self.date,
            'ref': 'Boleta de deposito: ' + name,
            'journal_id': self.journal_id.id,
        }
        move = self.env['account.move'].create(vals)

        # Hacemos el computo multimoneda
        company = self.env.user.company_id
        debit, credit, amount_currency, currency_id = self.env['account.move.line'].with_context(date=self.date).\
            compute_amount_fields(self.total, self.currency_id, company.currency_id)

        # Creamos los las lineas de los asientos
        self._create_move_lines(move, amount_currency, debit=debit)
        self._create_move_lines(move, -amount_currency, credit=debit)
        move.post()
        return move

    def _create_move_lines(self, move, amount_currency, debit=0.0, credit=0.0):
        """
        Crea una move line de la boleta de deposito y las asocia al move
        :param move: account.move - Asiento a relacionar las move_lines creadas
        :param debit: Importe en el haber de la move line
        :param credit: Importe en el haber de la move line
        :return: account.move.line creada
        """

        check_account_id = self.env.user.company_id.third_check_account_id
        account_id = self.journal_id.default_debit_account_id.id if debit else check_account_id.id
        company_currency = self.env.user.company_id.currency_id

        if not account_id:
            raise ValidationError("Falta configurar la cuenta de deposito en la cuenta bancaria"
                                  " o la de cheques de terceros en la compania")

        move_line_vals = {
            'move_id': move.id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency,
            'name': move.name,
            'account_id': account_id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != company_currency and self.currency_id.id or False,
            'ref': 'Boleta de deposito: ' + move.name
        }
        return self.env['account.move.line'].with_context(check_move_validity=False).create(move_line_vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
