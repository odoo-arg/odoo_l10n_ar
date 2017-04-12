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

from openerp import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

class CancelIssuedCheckWizard(models.TransientModel):

    _name = "cancel.issued.check.wizard"

    checkbook_check_id = fields.Many2one('account.checkbook.check', 'Cheque', required=True)
    checkbook_id = fields.Many2one('account.checkbook')

    @api.one
    def cancel_check(self):

        issued_check = self.env['account.issued.check']
        issued_check = issued_check.create({ 'number': 'ANULADO', 'checkbook_id': self.checkbook_id.id, 'amount': 0.0,
        'bank_id': self.checkbook_id.bank_id.id, 'issued': 'true', 'check_id':  self.checkbook_check_id.id,
        'account_bank_id': self.checkbook_id.bank_account_id.id, 'account_id': self.checkbook_id.account_id.id})

        return { 'type': 'ir.actions.act_window_close' }

CancelIssuedCheckWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
