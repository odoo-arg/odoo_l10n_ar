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

    name = fields.Char('Numero', required=True)
    bank_id = fields.Many2one('res.bank', 'Banco', required=True)
    payment_type = fields.Selection(
        [('common', 'Comun'),
         ('postdated', 'Diferido')],
        string="Tipo",
        required=True,
        default='common'
    )
    amount = fields.Monetary('Importe')
    currency_id = fields.Many2one('res.currency', 'Moneda')
    issue_date = fields.Date('Fecha de emision')
    payment_date = fields.Date('Fecha de pago')
    destination_payment_id = fields.Many2one(
        'account.payment',
        'Pago destino',
        help="Pago donde se utilizo el cheque"
    )

    @api.constrains('name')
    def constraint_name(self):
        if not self.name.isdigit():
            raise UserError("El numero del cheque debe contener solo numeros")

    @api.constrains('amount')
    def constraint_amount(self):
        if self.amount <= 0.0:
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


class AccountThirdCheck(models.Model):

    _inherit = 'account.abstract.check'
    _name = 'account.third.check'

    source_payment_id = fields.Many2one(
        'account.payment',
        'Recibo',
        help="Cobro desde donde se recibio el cheque",
        ondelete="cascade"
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
        default='draft'
    )
    issue_name = fields.Char('Nombre emisor')


class AccountIssuedCheck(models.Model):

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
        default='draft'
    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Chequera',
        required=True,
        ondelete='cascade'
    )
    account_own_check_line_ids = fields.One2many(
        'account.own.check.line',
        'own_check_id',
        'Lineas de pago',
        readonly=True
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
