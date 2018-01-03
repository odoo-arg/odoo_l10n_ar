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

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class AccountSoldCheck(models.Model):
    _name = 'account.sold.check'

    @api.depends('account_third_check_ids', 'interests', 'commission', 'account_third_check_ids')
    def _compute_amount(self):
        for sold_check in self:
            checks_amount = sum(check.amount for check in sold_check.account_third_check_ids)
            sold_check.amount = checks_amount - sold_check.interests - sold_check.commission

    name = fields.Char('Nombre', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    bank_account_id = fields.Many2one('account.journal', 'Cuenta bancaria')
    account_id = fields.Many2one(
        'account.account',
        'Cuenta para la acreditacion del dinero',
        required=True
    )
    journal_id = fields.Many2one('account.journal', 'Diario')
    date = fields.Date('Fecha de emision', required=True)
    commission = fields.Monetary('Importe de la comision')
    interests = fields.Monetary('Importe de los intereses')
    commission_account_id = fields.Many2one(
        'account.account',
        'Cuenta para las comisiones',
    )
    interest_account_id = fields.Many2one(
        'account.account',
        'Cuenta para los intereses'
    )
    amount = fields.Monetary('Total cobrado', compute=_compute_amount)
    account_third_check_ids = fields.Many2many(
        'account.third.check',
        'third_check_sold_check_rel',
        'sold_check_id',
        'third_check_id',
        string='Cheques',
    )
    move_id = fields.Many2one(
        'account.move',
        'Asiento contable',
        readonly=True
    )
    state = fields.Selection([
        ('canceled', 'Cancelado'),
        ('draft', 'Borrador'),
        ('sold', 'Vendido')
    ],
        default='draft',
        string='Estado',
        readonly=True
    )
    company_id = fields.Many2one('res.company', 'Compania')
    currency_id = fields.Many2one(
        'res.currency',
        'Moneda',
    )

    @api.constrains('interests', 'commission')
    def constrain_amount(self):
        if self.interests < 0 or self.commission < 0 or self.amount < 0:
            raise ValidationError("Los importes no pueden ser negativos")

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('account.sold.check.sequence')
        return super(AccountSoldCheck, self).create(values)

    @api.constrains('account_third_check_ids')
    def check_currency(self):
        """ Valida que no haya cheques con distintas monedas """
        for sold_check in self:
            currency = sold_check.account_third_check_ids.mapped('currency_id')
            if len(currency) > 1:
                raise ValidationError("No se pueden vender cheques de distintas monedas"
                                      " en el mismo documento de venta de cheques")

            sold_check.account_third_check_ids.sold_check_contraints()

    @api.multi
    def post(self):
        """ Confirma la venta de cheques cambiando el estado de los cheques y crea el asiento correspondiente """
        if not self.account_third_check_ids:
            raise ValidationError("No se puede validar una boleta sin cheques")
        for sold_check in self:
            sold_check._check_fields()
            sold_check.write({
                # Ya validamos en el constraint que la moneda es unica
                'currency_id': sold_check.account_third_check_ids.mapped('currency_id').id,
                'state': 'sold'
            })
            move = sold_check._create_move(sold_check.name)
            sold_check.move_id = move.id
            sold_check.account_third_check_ids.post_sold_check()

    def draft(self):
        """ Vuelve una la venta de cheques a estado borrador """
        self.ensure_one()
        self.state = 'draft'

    def cancel(self):
        """ Cancela la venta de cheques y elimina el asiento """

        self.ensure_one()
        # Cancelamos y borramos el asiento
        self.move_id.button_cancel()
        self.move_id.unlink()

        # Revertimos el estado de los cheques
        self.account_third_check_ids.cancel_sold_check()
        self.state = 'canceled'

    def _create_move(self, name):
        """
        Crea el asiento de la venta de cheques
        :param name: Referencia que se utilizará en el asiento
        :return: account.move creado
        """

        journal = self.bank_account_id or self.journal_id
        vals = {
            'date': self.date,
            'ref': 'Venta de cheques: {}'.format(name),
            'journal_id': journal.id,
        }
        move = self.env['account.move'].create(vals)
        account = self.account_id


        # Creamos las lineas del debe, puede haber hasta 3 (si tiene comision e intereses)
        if self.amount:
            amount, amount_currency = self._get_multicurrency_values(self.amount)
            self._create_move_lines(move, amount_currency, account, debit=amount)

        if self.commission:
            commission, amount_currency = self._get_multicurrency_values(self.commission)
            self._create_move_lines(move, amount_currency, self.commission_account_id, debit=commission)

        if self.interests:
            interests, amount_currency = self._get_multicurrency_values(self.interests)
            self._create_move_lines(move, amount_currency, self.interest_account_id, debit=interests)

        # Creamos la linea del haber
        amount, amount_currency = self._get_multicurrency_values(self.amount+self.interests+self.commission)
        self._create_move_lines(move, -amount_currency, self.env.user.company_id.third_check_account_id, credit=amount)

        move.post()

        return move

    def _create_move_lines(self, move, amount_currency, account, debit=0.0, credit=0.0):
        """
        Crea una move line de la venta de cheques y las asocia al move
        :param move: account.move - Asiento a relacionar las move_lines creadas
        :param amount_currency: Importe en moneda original
        :param account: Cuenta contable de la linea del asiento
        :param debit: Importe en el haber de la move line
        :param credit: Importe en el haber de la move line
        :return: account.move.line creada
        """

        company_currency = self.env.user.company_id.currency_id
        journal = self.bank_account_id or self.journal_id
        if not account:
            raise ValidationError("Falta configurar alguna cuenta contable para realizar esta tarea")

        move_line_vals = {
            'move_id': move.id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency,
            'name': move.ref,
            'account_id': account.id,
            'journal_id': journal.id,
            'currency_id': self.currency_id != company_currency and self.currency_id.id or False,
            'ref': move.ref
        }
        return self.env['account.move.line'].with_context(check_move_validity=False).create(move_line_vals)

    def _get_multicurrency_values(self, amount):
        """
        Devuelve el importe en multi moneda para la fecha de la venta de cheques
        :param amount: Importe a calcular en multi moneda
        :returns:  amount_currency - Importe en la moneda de la venta de cheque
                   debit - Importe para la move line

        """
        move_line_proxy = self.env['account.move.line']
        company = self.env.user.company_id

        debit, credit, amount_currency, currency_id = move_line_proxy.with_context(date=self.date). \
            compute_amount_fields(amount, self.currency_id, company.currency_id)

        return debit, amount_currency

    def _check_fields(self):
        """ Valida que el documento tenga la información necesaria para ser validado """
        self.ensure_one()
        if not (self.partner_id or self.bank_account_id):
            raise ValidationError("Debe seleccionar un partner o una cuenta bancaria para validar el documento")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
