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
import time
from dateutil import parser
from openerp import netsvc
import logging
_logger = logging.getLogger(__name__)


class wizard_account_collect_check(osv.osv_memory):

    _name = "wizard.account.collect.check"

    _columns = {

        #Datos para el cobro
        'name': fields.char(string='Collect check'),
        'date': fields.date('Collect date', required=True),
        'journal_id': fields.many2one('account.journal', 'Journal', domain=[('type','in',('cash', 'bank'))], required=True),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank account', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'account_id': fields.many2one('account.account', 'Account for accreditation of money', domain=[('type', '!=', 'view')], required=True),

        #Datos del cheque

        'check_id': fields.many2one('account.checkbook.check', 'Check', domain=[('state', '=', 'draft')]),
        'amount': fields.float('Check amount', required=True),
        'type': fields.selection([('common', 'Common'),('postdated', 'Post-dated')], 'Check Type', help="If common, checks only have issued_date. If post-dated they also have payment date"),
        'issue_date': fields.date('Issue date'),
        'payment_date': fields.date('Payment date'),


    }

    _defaults = {

        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'type': 'common',
    }


    def action_collect_check(self, cr, uid, ids, context=None):

        issued_check = self.pool.get('account.issued.check')
        move_line = self.pool.get('account.move.line')
        account_checkbook_obj = self.pool.get('account.checkbook.check')


        wizard = self.browse(cr, uid, ids[0], context=context)

        period_id = self.pool.get('account.period').find(cr, uid, wizard.date)[0]
        collect_date = wizard.date or time.strftime('%Y-%m-%d')

        if not wizard.bank_account_id.account_id:
            raise osv.except_osv(_("Error"), _("You have to configure an account on Bank Account %s: %s") % (wizard.bank_account_id.bank_name, wizard.bank_account_id.acc_number))

        #Collect_check

        if context is None:
            context = {}



        if wizard.payment_date > wizard.date:
            raise osv.except_osv(_("Cannot collect"), _("You cannot collect check %s because Payment Date is greater than Collect Date.") % (wizard.check_id.name))


        issued_check.create(cr, uid, { 
            'number': wizard.check_id.name, 
            'checkbook_id': wizard.check_id.checkbook_id.id,
            'type': wizard.type, 
            'amount': wizard.amount,
            'receiving_partner_id': wizard.company_id.partner_id.id, 
            'bank_id': wizard.check_id.checkbook_id.bank_id.id, 
            'issue_date': wizard.issue_date,
            'payment_date': wizard.payment_date, 
            'account_bank_id': wizard.check_id.checkbook_id.bank_account_id.id, 
            'issued': 'true',
            'check_id': wizard.check_id.id, 
            'account_id': wizard.check_id.checkbook_id.account_id.id 
        }, context=context)

        account_checkbook_obj.write(cr, uid, wizard.check_id.id, {'state': 'done'}, context=context)

        name = self.pool.get('ir.sequence').next_by_id(cr, uid, wizard.journal_id.sequence_id.id, context=context)

        move_id = self.pool.get('account.move').create(cr, uid, {
            'name': name,
            'journal_id': wizard.journal_id.id,
            'state': 'draft',
            'period_id': period_id,
            'date': collect_date,
            'ref': _('Check Collected Number %s') % wizard.check_id.name,
        })

        move_line.create(cr, uid, {
            'name': name,
            'centralisation': 'normal',
            'account_id': wizard.account_id.id,
            'move_id': move_id,
            'journal_id': wizard.journal_id.id,
            'period_id': period_id,
            'date': collect_date,
            'debit': wizard.amount,
            'credit': 0.0,
            'ref': _('Check Collected Number %s') % wizard.check_id.name,
            'state': 'valid',
        })

        move_line.create(cr, uid, {
            'name': name,
            'centralisation': 'normal',
            'account_id': wizard.check_id.checkbook_id.account_id.id,
            'move_id': move_id,
            'journal_id': wizard.journal_id.id,
            'period_id': period_id,
            'date': collect_date,
            'debit': 0.0,
            'credit': wizard.amount,
            'ref': _('Check Collected Number %s') % wizard.check_id.name,
            'state': 'valid',
        })

        # Se postea el asiento llamando a la funcion post de account_move.
        self.pool.get('account.move').post(cr, uid, [move_id], context=context)

        return { 'type': 'ir.actions.act_window_close' }

wizard_account_collect_check()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

