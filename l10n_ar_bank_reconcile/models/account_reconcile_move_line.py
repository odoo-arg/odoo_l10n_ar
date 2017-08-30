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

from openerp import models, fields, api


class AccountReconcileMoveLine(models.Model):
    _name = 'account.reconcile.move.line'

    bank_reconcile_line_id = fields.Many2one(
        comodel_name='account.bank.reconcile.line',
        string='Conciliacion',
        ondelete='cascade'
    )
    move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Apunte contable',
        ondelete='restrict'
    )
    name_move = fields.Char(
        related='move_line_id.move_id.name',
        string='Asiento contable'
    )
    ref_move = fields.Char(
        related='move_line_id.move_id.ref',
        string='Referencia'
    )
    name_move_line = fields.Char(
        related='move_line_id.name',
        string='Nombre'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        related='move_line_id.currency_id',
    )
    debit_move_line = fields.Monetary(
        related='move_line_id.debit',
        currency_field='currency_id',
        string='Debe'
    )
    credit_move_line = fields.Monetary(
        related='move_line_id.credit',
        currency_field='currency_id',
        string='Haber'
    )
    date_move_line = fields.Date(
        related='move_line_id.date',
        string='Fecha'
    )

    @api.multi
    def unlink(self):
        for reconcile_move_line in self:
            reconcile_move_line.move_line_id.bank_reconciled = False
        return super(AccountReconcileMoveLine, self).unlink()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
