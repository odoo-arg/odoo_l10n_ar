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


class AccountCheckCollectWizard(models.TransientModel):

    _name = "account.check.collect.wizard"

    payment_date = fields.Date(
        string='Fecha de pago',
        required=True,
    )

    collect_date = fields.Date(
        string='Fecha de cobro',
        required=True,
    )

    issue_date = fields.Date(
        string='Fecha de emision',
        required=True,
    )

    amount = fields.Float(
        string='Monto',
        required=True,
    )

    journal_id = fields.Many2one(
        'account.journal',
        string="Diario",
        required=True,
    )

    account_id = fields.Many2one(
        'account.account',
        string="Cuenta acreedora",
        required=True,
    )

    def _create_collect_move(self, check, ref):

        move_proxy = self.env['account.move']
        move_line_proxy = self.env['account.move.line']

        current_currency = check.currency_id
        company_currency = self.env.user.company_id.currency_id

        move_currency = current_currency.id if current_currency != company_currency else False

        debit, credit, amount_currency, currency_id = move_line_proxy.with_context(date=self.collect_date).compute_amount_fields(
            self.amount,
            current_currency,
            company_currency,
        )

        # La funcion anterior te devuelve el valor en credit o debit dependiendo
        # del signo de monto por lo tanto aca dejamos que credit sea igual que debit
        # simplemente a modo que sea mas comprensible la creacion de lineas de asiento
        credit = debit

        account_id = check.checkbook_id.account_id.id or check.checkbook_id.journal_id.default_credit_account_id.id
        if not account_id:
            raise ValidationError("La cuenta bancaria no tiene cuentas contables configuradas.\n"
                                  "Por favor, configurarla en el diario correspondiente o en la chequera")

        move_credit_vals = {
            'account_id': account_id,
            'credit': credit,
            'debit': 0.0,
            'name': ref,
            'amount_currency': -amount_currency,
            'currency_id': move_currency,
        }

        move_debit_vals = {
            'account_id': self.account_id.id,
            'debit': debit,
            'credit': 0.0,
            'name': ref,
            'amount_currency': amount_currency,
            'currency_id': move_currency,
        }

        move_vals = {
            'ref': ref,
            'journal_id': self.journal_id.id,
            'date': self.collect_date,
            'line_ids': [
                (0, 0, move_credit_vals),
                (0, 0, move_debit_vals),
            ]
        }

        move = move_proxy.create(move_vals)

        move.post()

        return move

    def collect_check(self):

        for wizard in self:

            check = self.env['account.own.check'].browse(self.env.context.get('active_id'))

            COLLECT_CHECK_REF = 'Cobro de cheque {check}'

            ref = COLLECT_CHECK_REF.format(
                check=check.name_get()[0][1],
                checkbook=check.checkbook_id.name_get()[0][1]
            )
            move = self._create_collect_move(check, ref)

            vals = {
                'amount': wizard.amount,
                'payment_date': wizard.payment_date,
                'collect_date': wizard.collect_date,
                'issue_date': wizard.issue_date,
                'collect_move_id': move.id,
            }

            check.post_collect(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
