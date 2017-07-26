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

from openerp import models, api
from openerp.exceptions import ValidationError


class AccountThirdCheck(models.Model):

    _inherit = 'account.third.check'

    def button_reject_check(self):
        """
        Se rechaza el cheque si esta en los estados correspondientes para ser rechazado
        :raise ValidationError: No esta en alguno de los estados para ser rechazado
        """
        self.ensure_one()
        self.reject_check()

        # TODO: Agregar funcionalidad de creacion de nota de debito

    def button_revert_reject(self):
        """
        Revierte el rechazo de un cheque
        :raise ValidationError: El estado del cheque no es rechazado
        """
        self.ensure_one()
        self.revert_reject()

    @api.multi
    def reject_check(self):
        """ Lo que deberia pasar con el cheque cuando se rechaza"""
        if any(check.state == 'draft' for check in self):
            raise ValidationError("No se puede rechazar un cheque en borrador")

        for check in self:
            # Se puede pasar a rechazado desde cartera, entregado o depositado
            check.next_state(check.state if check.state != 'wallet' else 'wallet_rejected')

    @api.multi
    def revert_reject(self):
        """ Lo que deberia pasar con el cheque cuando se revierte un rechazo """
        if any(check.state != 'rejected' for check in self):
            raise ValidationError("Funcionalidad unica para cheques rechazados")

        for check in self:

            # Si antes de rechazarse estaba depositado...
            if check.deposit_slip_id:
                check.cancel_state('rejected_deposited')

            # Si antes de rechazarse se lo dimos a un proveedor...
            elif check.destination_payment_id and check.destination_payment_id.state != 'draft':
                check.cancel_state('rejected_handed')

            # Si no estaba depositado o entregado deberia volver a cartera...
            else:
                check.cancel_state('rejected_wallet')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
