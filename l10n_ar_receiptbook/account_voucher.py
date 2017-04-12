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
from openerp import netsvc, api
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError
from openerp.tools.translate import _
import re

class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    _columns = {

        'reference': fields.char('Reference', size=13,readonly=True, states={'draft':[('readonly',False)]}, help="Transaction reference number."),
        'receiptbook_id': fields.many2one('account.receiptbook', 'Receiptbook', required=True),
    
    }

    def _get_receiptbook(self, cr, uid, context=None):

        receiptbook = None

        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
                
        cr.execute("SELECT 1 FROM account_receiptbook WHERE company_id = %s ORDER BY priority " % (company_id))
        receiptbook = cr.fetchone()
        if receiptbook:
            receiptbook = receiptbook[0]
        return receiptbook

    _defaults = {

        'receiptbook_id': _get_receiptbook,

    }

    @api.one
    @api.constrains('type', 'reference', 'receiptbook_id')
    def _check_duplicate(self):

        if self.type in ('receipt'):

            count = self.search_count([('receiptbook_id','=', self.receiptbook_id.id), ('reference','!=', False), ('reference','!=',''), ('reference','=',self.reference), ('type','=',self.type)])

            if count > 1:

                raise ValidationError(_('Error! The Voucher is duplicated.'))

    def reference_action(self, cr, uid, ids, context=None):
        voucher_number = None
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type != 'purchase':
                if not voucher.reference:
                    voucher_number = self._get_next_reference_number(cr, uid, voucher, context=context)
                    reference = voucher.receiptbook_id.name + '-' + str(voucher_number).zfill(8) #Llena con 0s hasta completar 8
                    self.write(cr, uid, voucher.id, {'reference': reference}, context=context)
                else:
                    form = re.match('^[0-9]{4}-[0-9]{8}$', voucher.reference)

                    if voucher.reference[0:4] != voucher.receiptbook_id.name:
                        raise osv.except_osv( _('Error'), _('This voucher reference is for another receiptbook')) 
                        
                    if not form:
                        raise osv.except_osv( _('Error'), _('The Voucher Number should be the format XXXX-XXXXXXXX'))
        return True

    def _get_next_reference_number(self, cr, uid, voucher, context=None):
        cr.execute("select max(to_number(substring(reference from '[0-9]{8}$'), '99999999')) from account_voucher where reference ~ '^[0-9]{4}-[0-9]{8}$' and receiptbook_id=%s and state in %s and type=%s ", (voucher.receiptbook_id.id, ('cancel', 'proforma', 'posted'), voucher.type))
        last_number = cr.fetchone()
        if not last_number or not last_number[0]:
            next_number = 1
        else:
            next_number = int(last_number[0]) + 1
        return next_number

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
