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

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class AccountDepositSlip(models.Model):

    _name = "account.deposit.slip"
    _inherit = ['mail.thread']

    @api.depends('check_ids')
    def _get_checks_total(self):
        for each in self:
            each.amount = sum(check.amount for check in each.check_ids)

    name = fields.Char(
        string='Boleta de deposito',
        readonly=True,
        track_visibility='onchange'
    )
    date = fields.Date(
        'Fecha',
        required=True,
        track_visibility='onchange'
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Cuenta Bancaria',
        required=True,
        track_visibility='onchange'
    )
    amount = fields.Monetary(
        'Importe total',
        compute='_get_checks_total',
        track_visibility='onchange'
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Moneda',
        track_visibility='onchange'
    )
    check_ids = fields.Many2many(
        'account.third.check',
        'third_check_deposit_slip_rel',
        'deposit_slip_id',
        'third_check_id',
        string='Cheques'
    )
    state = fields.Selection(
        [('canceled', 'Cancelada'),
         ('draft', 'Borrador'),
         ('deposited', 'Depositada')],
        string='Estado',
        default='draft',
        track_visibility='onchange'
    )
    move_id = fields.Many2one(
        'account.move',
        'Asiento contable',
        readonly=True,
        track_visibility='onchange'
    )

    _sql_constraints = [('name_uniq', 'unique(name)', 'El nombre de la boleta de deposito debe ser unico')]

    _order = "date desc, name desc"

    @api.constrains('check_ids')
    def check_currency(self):
        """ Valida que no haya cheques con distintas monedas """
        for deposit_slip in self:
            currency = deposit_slip.check_ids.mapped('currency_id')
            if len(currency) > 1:
                raise ValidationError("No se pueden depositar cheques de distintas monedas"
                                      " en la misma boleta de deposito")

            deposit_slip.check_ids.deposit_slip_contraints()

    @api.multi
    def post(self):
        """ Confirma la boleta de deposito cambiando el estado de los cheques y crea el asiento correspondiente """
        for deposit_slip in self:
            if not self.check_ids:
                raise ValidationError("No se puede validar una boleta sin cheques")

            deposit_slip.write({
                # Ya validamos en el constraint que la moneda es unica
                'currency_id': deposit_slip.check_ids.mapped('currency_id').id,
                'state': 'deposited'
            })
            move = deposit_slip._create_move(deposit_slip.name)
            deposit_slip.move_id = move.id
            deposit_slip.check_ids.post_deposit_slip()

    def cancel_to_draft(self):
        """ Vuelve una boleta a estado borrador """
        self.ensure_one()
        self.state = 'draft'

    def cancel_deposit_slip(self):
        """ Cancela la boleta de deposito y elimina el asiento """

        self.ensure_one()
        # Cancelamos y borramos el asiento
        self.move_id.button_cancel()
        self.move_id.unlink()

        # Revertimos el estado de los cheques
        self.check_ids.cancel_deposit_slip()

        self.state = 'canceled'

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('account.deposit.slip.sequence')
        return super(AccountDepositSlip, self).create(values)

    def _create_move(self, name):
        """
        Crea el asiento de la boleta de deposito
        :param name: Nombre del asiento
        :return: account.move creado
        """

        vals = {
            'date': self.date,
            'ref': 'Boleta de deposito: ' + name,
            'journal_id': self.journal_id.id,
        }
        move = self.env['account.move'].create(vals)

        # Hacemos el computo multimoneda
        company = self.env.user.company_id
        debit, credit, amount_currency, currency_id = self.env['account.move.line'].with_context(date=self.date).\
            compute_amount_fields(self.amount, self.currency_id, company.currency_id)

        # Creamos las lineas de los asientos
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
            'name': move.ref,
            'account_id': account_id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != company_currency and self.currency_id.id or False,
            'ref': move.ref
        }
        return self.env['account.move.line'].with_context(check_move_validity=False).create(move_line_vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
