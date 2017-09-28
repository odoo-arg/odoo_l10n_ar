# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import Warning, ValidationError


class AccountAbstractPayment(models.Model):

    _inherit = 'account.abstract.payment'

    payment_imputation_ids = fields.One2many('payment.imputation.line', 'Imputaciones')

    def reconcile_invoices(self, move_line):

        # Borramos las imputaciones que no se van a realizar
        self.payment_imputation_ids.filtered(lambda x: not x.amount).unlink()

        for imputation in self.payment_imputation_ids:

            invoice_move_line = imputation.invoice_id.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable')
            )
            # Caso que se modifique el asiento y deje inconsistencia
            if len(invoice_move_line) != 1:
                raise ValidationError("El asiento de la factura que se quiere imputar no tiene cuentas deudoras "
                                      "o tiene mas de una asociada, por favor, modificar el asiento primero")

            debit_move = move_line if move_line.debit > 0 else invoice_move_line
            credit_move = move_line if move_line.credit > 0 else invoice_move_line

            amount_reconcile_currency = 0
            currency = False
            amount_reconcile = min(debit_move.amount_residual_currency, -credit_move.amount_residual_currency)

            if debit_move.currency_id == credit_move.currency_id and debit_move.currency_id:
                currency = credit_move.currency_id
                amount_reconcile_currency = min(
                    debit_move.amount_residual_currency,
                    -credit_move.amount_residual_currency
                )

            self.env['account.partial.reconcile'].create({
                'debit_move_id': debit_move.id,
                'credit_move_id': credit_move.id,
                'amount': amount_reconcile,
                'amount_currency': amount_reconcile_currency,
                'currency_id': currency,
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
