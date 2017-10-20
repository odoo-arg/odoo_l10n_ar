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
from openerp.exceptions import Warning


class account_bank_reconcile_line(models.Model):
    _name = "account.bank.reconcile.line"

    period_id = fields.Many2one('account.period', 'Period', readonly=True)
    last_balance = fields.Float('Last Balance', readonly=True)
    last_balance_currency = fields.Float('Balance anterior en moneda', readonly=True)
    current_balance = fields.Float('Current Balance', readonly=True)
    current_balance_currency = fields.Float('Balance actual en moneda', readonly=True)
    move_line_ids = fields.One2many('account.move.line', 'bank_reconcile_line_id', 'Move lines')
    bank_reconcile_id = fields.Many2one('account.bank.reconcile', 'Bank reconcile', readonly=True, ondelete="cascade")
    last = fields.Boolean('Ultimo')

    @api.multi
    def write(self, values):
        """ 
        Sobreescribimos el write para los casos que se seleccione que se desea eliminar una linea de conciliacion
        """
        removed_ids = []
        # Buscamos que en los valores del write se quiera escribir algun cambio de las lineas
        if values.get('move_line_ids'):

            for line in values.get('move_line_ids'):

                # En el caso que se hallan escrito las lineas y esten tildadas para borrar se borra
                if line[2] is not False and line[2].get('delete_from_conciliation'):
                    removed_ids.append(line[1])
                    line[2]['is_reconciled'] = False
                    line[2]['bank_reconcile_line_id'] = False
                    line[2]['delete_from_conciliation'] = False

        # Recalculamos el balance
        if not (values.get('current_balance') or values.get('current_balance_currency')):

            balance = self.current_balance
            balance_currency = self.current_balance_currency
            for line in self.move_line_ids.filtered(lambda x: x.id in (removed_ids)):
                balance -= line.debit - line.credit
                balance_currency -= line.amount_currency

            # TODO: se podria hacer campo funcion pero la idea es que no se modifique el balance
            # Ya que el usuario lo valida y lo chequea, de esta forma nos aseguramos que no se modifique
            values['current_balance'] = balance
            values['current_balance_currency'] = balance_currency

        super(account_bank_reconcile_line, self).write(values)

    @api.one
    def unlink(self):
        """
        Redefinition of unlink method so the move lines are visible again
        """
        self.move_line_ids.write({'is_reconciled': False})
        if self.bank_reconcile_id._get_last_conciliation() != self:
            raise Warning('No se puede borrar un periodo que no es el mayor!')

        bank_reconcile = self.bank_reconcile_id
        res = super(account_bank_reconcile_line, self).unlink()

        if bank_reconcile.bank_reconcile_line_ids:
            bank_reconcile._get_last_conciliation().last = True

        return res

    _order = 'id desc'


account_bank_reconcile_line()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
