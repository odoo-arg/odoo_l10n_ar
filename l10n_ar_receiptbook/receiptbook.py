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

import time
from lxml import etree
from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_receiptbook(osv.osv):

    _name = 'account.receiptbook'

    _columns = {

        'name': fields.char('Number', required=True, size=4),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'priority' : fields.integer('Priority', required=True, size=6),
        'desc' : fields.char('Description', size=180),
        'print_type': fields.selection( ([('preprinted','Preimpreso'),('fiscal_printer','Impresora Fiscal')]),required=True, string="Print Type"),

    }

    _defaults = {

        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='account.receiptbook',context=ctx),
        'print_type': lambda *args: 'preprinted',

    }

    def _check_name(self, cr, uid, ids, context=None):
        for receiptbook in self.browse(cr, uid, ids, context=context):
            if len(receiptbook.name) < 4 :
                return False
        return True

    _constraints = [

        (_check_name, 'Wrong number. Should be compose of 4 numbers',[])

    ]

account_receiptbook()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
