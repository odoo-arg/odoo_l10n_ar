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


class AccountOwnCheck(models.Model):

    _inherit = 'account.own.check'

    @api.multi
    def cancel_check(self):
        """ Lo que deberia pasar con el cheque cuando se rechaza """
        if any(check.state != 'draft' for check in self):
            raise ValidationError("Solo se puede cancelar un cheque en estado borrador")
        self.next_state('draft_canceled')

    @api.multi
    def revert_canceled_check(self):
        """ Lo que deberia pasar con el cheque cuando se revierte un rechazo """
        if any(check.state != 'canceled' for check in self):
            raise ValidationError("Funcionalidad unica para cheques cancelados")
        self.cancel_state('canceled')

    @api.multi
    def reject_check(self):
        """ Lo que deberia pasar con el cheque cuando se rechaza """
        if any(check.state != 'handed' for check in self):
            raise ValidationError("No se puede rechazar un cheque que no esta entregado")
        self.next_state('handed')

    @api.multi
    def revert_reject(self):
        """ Lo que deberia pasar con el cheque cuando se revierte un rechazo """
        if any(check.state != 'rejected' for check in self):
            raise ValidationError("Funcionalidad unica para cheques rechazados")
        self.cancel_state('rejected')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
