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


class AccountDepositSlip(models.Model):

    _name = "account.deposit.slip"

    name = fields.Char(
        string='Boleta de deposito',
        required=True,
        readonly=True,
    )
    date = fields.Date(
        'Fecha',
        readonly=True
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Cuenta Bancaria',
        required=True
    )
    amount = fields.Monetary(
        'Importe total',
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        'Moneda',
        required=True,
    )
    checks_ids = fields.One2many(
        'account.third.check',
        'deposit_slip_id',
        string='Cheques',
        readonly=True
    )
    state = fields.Selection(
        [('canceled', 'Cancelada'),
         ('deposited', 'Depositada')],
        string='Estado'
    )
    move_id = fields.Many2one(
        'account.move',
        'Asiento contable',
        readonly=True
    )

    _sql_constraints = [('name_uniq', 'unique(name)', 'El nombre de la boleta de deposito debe ser unico')]

    _order = "date desc, name desc"

    @api.multi
    def cancel_deposit_slip(self):
        """ Cancela la boleta de deposito y elimina el asiento """

        self.ensure_one()
        # Cancelamos y borramos el asiento
        self.move_id.button_cancel()
        self.move_id.unlink()

        # Revertimos el estado de los cheques
        self.checks_ids.cancel_deposit_slip()

        self.state = 'canceled'

AccountDepositSlip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
