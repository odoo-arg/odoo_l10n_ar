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

    def action_create_deposit_slip(self):
        """
        Crea la boleta de deposito y relaciona los cheques a la misma
        :return: Formulario de la boleta de deposito creada
        """

        deposit_slip = self._create_deposit_slip()

        return {
            'name': 'Boleta de deposito',
            'views': [[False, "form"]],
            'res_model': 'account.deposit.slip',
            'type': 'ir.actions.act_window',
            'res_id': deposit_slip.id,
        }

    def _create_deposit_slip(self):
        """
        Crea la boleta de deposito y la asocia al asiento
        :param name: Nombre de de la boleta de deposito
        :param move: Asiento asociado a la boleta de deposito
        :return: account.deposit.slip - Boleta de deposito creada
        """

        checks = self.env['account.third.check'].browse(self.env.context.get('active_ids'))

        deposit_slip = self.env['account.deposit.slip'].create({
            'date': self.date,
            'journal_id': self.journal_id.id,
            'amount': self.total,
            'check_ids': [(6, 0, checks.ids)],
            'state': 'draft',
            'currency_id': self.currency_id.id
        })
        return deposit_slip

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
