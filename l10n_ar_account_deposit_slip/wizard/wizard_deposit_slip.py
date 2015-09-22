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


class wizard_account_deposit_slip(osv.osv_memory):

    _name = "wizard.account.deposit.slip"

    _columns = {

        'name': fields.char(string='Deposit slip number',size=128),
        'date': fields.date('From', required=True),
        'bank_account_id': fields.many2one('res.partner.bank', 'Bank Account', required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'journal_id': fields.many2one('account.journal', 'Journal', domain=[('type','in',('cash', 'bank'))], required=True),

    }

    def _get_journal(self, cr, uid, context=None):
        journal_id = False
        voucher_obj = self.pool.get('account.voucher')
        model = context.get('active_model', False)
        if model and model == 'account.third.check':
            ids = context.get('active_ids', [])
            vouchers = self.pool.get(model).read(cr, uid, ids, ['source_voucher_id'], context=context)
            if vouchers and vouchers[0] and 'source_voucher_id' in vouchers[0]:
                if vouchers[0]['source_voucher_id']:
                    voucher_id = vouchers[0]['source_voucher_id'][0]
                    journal_id = voucher_obj.read(cr, uid, voucher_id, ['journal_id'], context=context)['journal_id'][0]
        return journal_id

    _defaults = {

        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'journal_id': _get_journal,

    }

    def _get_source_account_check(self, cr, uid, company_id):
        check_config_obj = self.pool.get('account.check.config')

        # Obtenemos la configuracion
        res = check_config_obj.search(cr, uid, [('company_id', '=', company_id)])
        if not len(res):
            raise osv.except_osv(_('Error!'), _('There is no check configuration for this Company!'))

        src_account = check_config_obj.read(cr, uid, res[0], ['account_id'])
        if 'account_id' in src_account:
            return src_account['account_id'][0]

        raise osv.except_osv(_('Error!'), _('Bad Treasury configuration for this Company!'))


    def action_deposit(self, cr, uid, ids, context=None):

        deposit_slip_obj = self.pool.get('account.deposit.slip')

        third_check = self.pool.get('account.third.check')
        wf_service = netsvc.LocalService('workflow')
        move_line = self.pool.get('account.move.line')
        wizard = self.browse(cr, uid, ids[0], context=context)

        period_id = self.pool.get('account.period').find(cr, uid, wizard.date)[0]
        deposit_date = wizard.date or time.strftime('%Y-%m-%d')

        if not wizard.bank_account_id.account_id:
            raise osv.except_osv(_("Error"), _("You have to configure an account on Bank Account %s: %s") % (wizard.bank_account_id.bank_name, wizard.bank_account_id.acc_number))

        #Deposit slip
        if context is None:
            context = {}

        active_ids = context.get('active_ids', [])
        company_id = wizard.company_id.id
        check_objs = third_check.browse(cr, uid, active_ids, context=context)

        deposit_slip_amount = 0
        checks = []

        for check in check_objs:

            if check.state != 'wallet':
                raise osv.except_osv(_("Error"), _("The selected checks must to be in cartera.\nCheck %s is not in wallet") % (check.number))

            if check.payment_date > deposit_date:
                raise osv.except_osv(_("Cannot deposit"), _("You cannot deposit check %s because Payment Date is greater than Deposit Date.") % (check.number))

            account_check_id = self._get_source_account_check(cr, uid, company_id)

            deposit_slip_amount += check.amount

            check_vals = {'deposit_bank_id': wizard.bank_account_id.id, 'deposit_date': deposit_date}
            check.write(check_vals)

            wf_service.trg_validate(uid, 'account.third.check', check.id, 'cartera_deposited', cr)

            checks.append(check.id)

        sequence = self.pool.get('ir.sequence').get(cr, uid, 'account.deposit.slip.sequence')

        deposit_slip_obj.create(cr, uid, {
            'name': sequence,
            'date': wizard.date,
            'bank_account_id': wizard.bank_account_id.id,
            'total_amount': deposit_slip_amount,
            'checks_ids': [(6, 0, checks)]
        })

        move_id = self.pool.get('account.move').create(cr, uid, {
            'name': sequence,
            'journal_id': wizard.journal_id.id,
            'state': 'draft',
            'period_id': period_id,
            'date': deposit_date,
            'ref': _('Deposit Slip Number %s') % sequence,
        })

        move_line.create(cr, uid, {
            'name': sequence,
            'centralisation': 'normal',
            'account_id': wizard.bank_account_id.account_id.id,
            'move_id': move_id,
            'journal_id': wizard.journal_id.id,
            'period_id': period_id,
            'date': deposit_date,
            'debit': deposit_slip_amount,
            'credit': 0.0,
            'ref': _('Deposit Slip Number %s') % sequence,
            'state': 'valid',
        })

        move_line.create(cr, uid, {
            'name': sequence,
            'centralisation': 'normal',
            'account_id': account_check_id,
            'move_id': move_id,
            'journal_id': wizard.journal_id.id,
            'period_id': period_id,
            'date': deposit_date,
            'debit': 0.0,
            'credit': deposit_slip_amount,
            'ref': _('Deposit Slip Number %s') % sequence,
            'state': 'valid',
        })

        # Se postea el asiento llamando a la funcion post de account_move.
        # TODO: Se podria poner un check en el wizard para que elijan si postear
        # el asiento o no.
        self.pool.get('account.move').post(cr, uid, [move_id], context=context)

        return { 'type': 'ir.actions.act_window_close' }

wizard_account_deposit_slip()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
