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
from openerp.exceptions import ValidationError, UserError


class AccountAbstractCheck(models.AbstractModel):

    _name = 'account.abstract.check'
    _inherit = ['mail.thread']

    name = fields.Char('Numero', required=True, track_visibility='onchange')
    bank_id = fields.Many2one('res.bank', 'Banco', required=True, track_visibility='onchange')
    payment_type = fields.Selection(
        [('common', 'Comun'),
         ('postdated', 'Diferido')],
        string="Tipo",
        required=True,
        default='common',
        track_visibility='onchange'
    )
    amount = fields.Monetary('Importe', track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', 'Moneda', track_visibility='onchange')
    issue_date = fields.Date('Fecha de emision', track_visibility='onchange')
    payment_date = fields.Date('Fecha de pago', track_visibility='onchange')
    destination_payment_id = fields.Many2one(
        'account.payment',
        'Pago destino',
        help="Pago donde se utilizo el cheque",
        track_visibility='onchange'
    )

    @api.constrains('name')
    def constraint_name(self):
        if not self.name.isdigit():
            raise UserError("El numero del cheque debe contener solo numeros")

    @api.constrains('amount')
    def constraint_amount(self):
        if self.amount < 0.0:
            raise ValidationError("El importe del cheque debe ser mayor a 0")

    @api.constrains('payment_date', 'issue_date', 'payment_type')
    def constraint_dates(self):
        if self.payment_date and self.payment_date < self.issue_date:
            raise ValidationError("La fecha de pago no puede ser menor a la fecha de emision")

        if self.payment_type == 'common' and self.payment_date != self.issue_date:
            raise ValidationError("Las fechas de pago y emision de los cheques comunes deben ser similares")

    @api.onchange('payment_type', 'issue_date')
    def onchange_payment_type(self):
        if self.payment_type == 'common' and self.issue_date:
            self.payment_date = self.issue_date


THIRD_CHECK_NEXT_STATES = {
    'draft': 'wallet',
    'wallet_deposited': 'deposited',
    'wallet_handed': 'handed',
    'wallet_rejected': 'rejected',
    'handed': 'rejected',
    'deposited': 'rejected',
}
THIRD_CHECK_CANCEL_STATES = {
    'wallet': 'draft',
    'handed': 'wallet',
    'deposited': 'wallet',
    'rejected_wallet': 'wallet',
    'rejected_handed': 'handed',
    'rejected_deposited': 'deposited',
}


class AccountThirdCheck(models.Model):

    _inherit = 'account.abstract.check'
    _name = 'account.third.check'

    source_payment_id = fields.Many2one(
        'account.payment',
        'Recibo',
        help="Cobro desde donde se recibio el cheque",
        ondelete="cascade",
        track_visibility='onchange'
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('wallet', 'En cartera'),
            ('handed', 'Entregado'),
            ('deposited', 'Depositado'),
            ('rejected', 'Rechazado')
        ],
        string='Estado',
        required=True,
        default='draft',
        track_visibility='onchange'
    )
    issue_name = fields.Char('Nombre emisor', track_visibility='onchange')

    @api.multi
    def post_receipt(self, currency_id):
        """ Lo que deberia pasar con el cheque cuando se valida un recibo.. """
        if any(check.state != 'draft' for check in self):
            raise ValidationError("Los cheques de terceros recibidos deben estar en estado borrador")
        self.write({'currency_id': currency_id})
        self.next_state('draft')

    @api.multi
    def post_payment(self):
        """ Lo que deberia pasar con el cheque cuando se valida un pago.. """
        if any(check.state != 'wallet' for check in self):
            raise ValidationError("Los cheques de terceros entregados deben estar en cartera")
        self.next_state('wallet_handed')

    @api.multi
    def cancel_receipt(self):
        """ Lo que deberia pasar con el cheque cuando se cancela un recibo.. """
        if any(check.state != 'wallet' for check in self):
            raise ValidationError("Los cheques de terceros recibidos deben estar en cartera para cancelar el pago")
        self.cancel_state('wallet')

    @api.multi
    def cancel_payment(self):
        """ Lo que deberia pasar con el cheque cuando se cancela una orden de pago.. """
        if any(check.state != 'handed' for check in self):
            raise ValidationError("Los cheques de terceros deben estar en estado entregado para cancelar el pago")
        self.cancel_state('handed')

    @api.multi
    def cancel_state(self, state):
        """ Vuelve a un estado anterior del flow del cheque si corresponde """
        cancel_state = THIRD_CHECK_CANCEL_STATES.get(state)
        if not cancel_state:
            raise ValidationError("No se puede cancelar el estado del cheque")
        self.write({'state': cancel_state})

    @api.multi
    def next_state(self, state):
        """ Avanza al siguiente estado del flow del cheque si corresponde """
        next_state = THIRD_CHECK_NEXT_STATES.get(state)
        if not next_state:
            raise ValidationError("No se puede avanzar el estado del cheque")
        self.write({'state': next_state})


OWN_CHECK_NEXT_STATES = {
    'draft_handed': 'handed',
    'draft_canceled': 'canceled',
    'handed': 'rejected',
}
OWN_CHECK_CANCEL_STATES = {
    'canceled': 'draft',
    'handed': 'draft',
    'rejected': 'handed'
}


class AccountOwnCheck(models.Model):

    _inherit = 'account.abstract.check'
    _name = 'account.own.check'

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('handed', 'Entregado'),
            ('canceled', 'Anulado'),
            ('rejected', 'Rechazado')
        ],
        string='Estado',
        required=True,
        default='draft',
        track_visibility='onchange'
    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Chequera',
        required=True,
        ondelete='cascade',
        track_visibility='onchange'
    )

    @api.multi
    def post_payment(self, vals):
        """ Lo que deberia pasar con el cheque cuando se valida el pago.. """
        if any(check.state != 'draft' for check in self):
            raise ValidationError("Los cheques propios entregados deben estar en estado borrador")

        vals = vals if vals else {}
        self.write(vals)
        self.next_state('draft_handed')

    @api.multi
    def cancel_payment(self):
        """ Lo que deberia pasar con el cheque cuando se cancela el pago.. """
        if any(check.state != 'handed' for check in self):
            raise ValidationError("Los cheques propios deben estar en estado entregado para cancelar el pago")
        self.cancel_state('handed')
        self.write({'destination_payment_id': None})

    @api.multi
    def cancel_state(self, state):
        """ Vuelve a un estado anterior del flow del cheque si corresponde """
        cancel_state = OWN_CHECK_CANCEL_STATES.get(state)
        if not cancel_state:
            raise ValidationError("No se puede cancelar el estado del cheque")
        self.write({'state': cancel_state})

    @api.multi
    def next_state(self, state):
        """ Avanza al siguiente estado del flow del cheque si corresponde """
        next_state = OWN_CHECK_NEXT_STATES.get(state)
        if not next_state:
            raise ValidationError("No se puede avanzar el estado del cheque")
        self.write({'state': next_state})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
