# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Eynes S.R.L. (http://www.eynes.com.ar) All Rights Reserved.
#    Copyright (c) 2014 Aconcagua Team (http://www.proyectoaconcagua.com.ar)
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
from openerp.osv import fields, osv
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_checkbook(osv.osv):

    _name = "account.checkbook"

    _description = "Checkbook"

    _columns = {

        'name': fields.char('Checkbook Number', size=32, required=True),
        'bank_id': fields.many2one('res.bank','Bank', required=True),
        'bank_account_id': fields.many2one('res.partner.bank','Bank Account', required=True),
        'check_ids': fields.one2many('account.checkbook.check', 'checkbook_id', 'Available Checks', domain=[('state','=','draft')], readonly=True),
        'issued_check_ids': fields.one2many('account.issued.check', 'checkbook_id', 'Issued Checks', readonly=True),
        'partner_id': fields.related('company_id', 'partner_id', type="many2one", relation="res.partner", string="Partner", store=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'type': fields.selection([('common', 'Common'),('postdated', 'Post-dated')], 'Checkbook Type', help="If common, checks only have issued_date. If post-dated they also have payment date"),
        'account_id': fields.many2one('account.account', 'Cuenta', required=True)
    }

    _defaults = {

        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'partner_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.partner_id.id,
        'type': 'common',

    }

    def onchange_bank_account(self, cr, uid, ids, bank_account_id, context=None):
        vals = {}
        if context is None:
            context = {}

        if not bank_account_id:
            return {'value': vals}

        bank_id = self.pool.get('res.partner.bank').read(cr, uid, bank_account_id, ['bank'], context)['bank']
        if bank_id:
            vals['bank_id'] = bank_id[0]

        return {'value': vals}

    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        for checkbook in self.browse(cr, uid, ids, context):
            if len(checkbook.issued_check_ids):
                raise osv.except_osv(_('Error'), _('You cannot delete this checkbook because it has Issued Checks'))

            super(account_checkbook, self).unlink(cr, uid, checkbook.id, context=context)

        return True

    @api.multi
    def cancel_check_on_checkbook(self):

        return {

            'name': _('Anular cheque'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cancel.issued.check.wizard',
            'views': [[False, "form"]],
            'target': 'new',
            'context': {'default_checkbook_id': self.id}
        }

account_checkbook()


class checkbook_check(osv.osv):

    """Relacion entre Chequera y cheques por nro de cheque"""
    _name = "account.checkbook.check"

    _description = "Checkbook Check"

    _columns = {

        'name': fields.char('Check Number', size=20, required=True),
        'checkbook_id': fields.many2one('account.checkbook', 'Checkbook number', ondelete='cascade', required=True),
        # Para tener una referencia a que cheque se convirtio
        #'issued_check_id': fields.many2one('account.issued.check', 'Issued Check', readonly=True),
        'state': fields.selection([('draft', 'Draft'),('done', 'Used')],
                                    'State', readonly=True),
    }

    _defaults = {

        'state': 'draft'

    }

checkbook_check()


class account_issued_check(osv.osv):

    _inherit = 'account.issued.check'

    _columns = {

        'check_id': fields.many2one('account.checkbook.check', 'Check'),
        'checkbook_id': fields.many2one('account.checkbook', 'Checkbook'),
        'number': fields.char('Check Number', size=20),
        'account_id': fields.many2one('account.account', 'Cuenta', required=True),
        'rejected': fields.boolean('Rechazado'),
        'reject_move_id': fields.many2one('account.move', 'Asiento de rechazo')

    }

    @api.multi
    def reject_issued_check(self):

        return {

            'name': _('Rechazar cheque'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'reject.issued.check.wizard',
            'views': [[False, "form"]],
            'target': 'new',
        }

    def on_change_check_id(self, cr, uid, ids, check_id, context=None):
        if context is None:
            context = {}
        if not check_id:
            return {'value':{}}

        check = self.pool.get('account.checkbook.check').browse(cr, uid, check_id, context=context)
        checkbook = check.checkbook_id

        return {'value':{'account_bank_id': checkbook.bank_account_id.id, 'checkbook_id': checkbook.id,
                         'bank_id': checkbook.bank_id.id, 'number': check.name, 'type': checkbook.type,
                         'account_id': checkbook.account_id.id}}

    def write(self, cr, uid, ids, vals, context=None):
        a = vals.get('check_id', False)
        if a:
            sql = 'select check_id from account_issued_check where id = ' + str(ids[0])
            cr.execute(sql)
            aux_check_id = cr.fetchone()
            self.pool.get('account.checkbook.check').write(cr, uid, aux_check_id, {'state': 'draft'})
            self.pool.get('account.checkbook.check').write(cr, uid, a, {'state': 'done'})
        return super(account_issued_check, self).write(cr, uid, ids, vals, context=context)

    def create(self, cr, uid, vals, context=None):
        a = vals.get('check_id', False)
        if a:
            self.pool.get('account.checkbook.check').write(cr, uid, a, {'state': 'done'})
        return super(account_issued_check, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        sql = 'select check_id from account_issued_check where id = ' + str(ids[0])
        cr.execute(sql)
        aux_check_id = cr.fetchone()
        self.pool.get('account.checkbook.check').write(cr, uid, aux_check_id, {'state': 'draft'})
        return super(account_issued_check, self).unlink(cr, uid, ids, context=context)

    #Misma función que en el módulo de cheques, solo que la cuenta no la va a buscar al banco ahora
    def create_voucher_move_line(self, cr, uid, check, voucher, context={}):
        voucher_obj = self.pool.get('account.voucher')

        account_id = check.account_id.id
        if not account_id:
            raise osv.except_osv(_("Error"), _("Bank Account has no account configured. Please, configure an account for the bank account used for checks!"))

        company_currency = voucher.company_id.currency_id.id
        current_currency = voucher.currency_id.id

        amount_in_company_currency =  voucher_obj._convert_paid_amount_in_company_currency(cr, uid, voucher, check.amount, context=context)

        debit = credit = 0.0
        if voucher.type in ('purchase', 'payment'):
            credit = amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        # Creamos la linea contable perteneciente al cheque
        move_line = {

            'name': 'Cheque propio ' + check.number or '/',
            'debit': debit,
            'credit': credit,
            'account_id': account_id,
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': company_currency <> current_currency and  current_currency or False,
            'amount_currency': company_currency <> current_currency and sign * check.amount or 0.0,
            'date': voucher.date,
            'date_maturity': voucher.date_due

        }

        return move_line
    
    _sql_constraints = [('unique_number','unique (check_id, checkbook_id)', 'Ya existe una cheque con ese numero para esa chequera')]
    
account_issued_check()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
