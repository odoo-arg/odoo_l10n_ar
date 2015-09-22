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

from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_deposit_slip(osv.osv):

    _name = "account.deposit.slip"

    _description = 'Deposit slip'

    _columns = {

        'name':fields.char(string='Deposit slip number',size=128, select=True, required=True, readonly=True, ondelete='set null'),
        'date': fields.date('Deposit slip date',readonly=True),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account',required=True),
        'total_ammount':fields.float('Total Ammount',readonly=True),
        'checks_ids':fields.one2many('account.third.check','deposit_slip_id',string='Check Lines', readonly=True),

    }

    _sql_constraints = [('name_uniq','unique(name)','The name must be unique!')]

    _order = "date desc"

account_deposit_slip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
