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
from openerp import api
import openerp.addons.decimal_precision as dp
import time


class retention_tax_line(osv.osv):

    _name = "retention.tax.line"

    _description = "Retention Tax Line"

    _columns = {

        'name': fields.char('Retention', size=64),
        'date': fields.date('Date', select=True),
        'voucher_id': fields.many2one('account.voucher', 'Voucher', ondelete='cascade'),
        'voucher_number': fields.char('Reference', size=64),
        'account_id': fields.many2one('account.account', 'Tax Account', required=True,
                                      domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'retention_id': fields.many2one('retention.retention', 'Retention Configuration', required=True, help="Retention configuration used '\
                                       'for this retention tax, where all the configuration resides. Accounts, Tax Codes, etc."),
        'base_code_id': fields.many2one('account.tax.code', 'Base Code', help="The account basis of the tax declaration."),
        'base_amount': fields.float('Base Code Amount', digits_compute=dp.get_precision('Account')),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', help="The tax basis of the tax declaration."),
        'tax_amount': fields.float('Tax Code Amount', digits_compute=dp.get_precision('Account')),
        'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'certificate_no': fields.char('Certificate No.', required=False, size=32),
        'state_id': fields.many2one('res.country.state', string="State/Province"),
        'vat': fields.related('partner_id', 'vat', type='char', string='CIF/NIF', readonly=True),
        'regimen': fields.char('Regimen'),
        'regimen_code': fields.integer('Regimen Code'),

    }

    def onchange_retention(self, cr, uid, ids, retention_id, context):
        if not retention_id:
            return {}

        retention_obj = self.pool.get('retention.retention')
        retention = retention_obj.browse(cr, uid, retention_id)
        vals = {}
        vals['name'] = retention.name
        vals['account_id'] = retention.tax_id.account_collected_id.id
        vals['base_code_id'] = retention.tax_id.base_code_id.id
        vals['tax_code_id'] = retention.tax_id.tax_code_id.id

        if retention.state_id:
            vals['state_id'] = retention.state_id.id
        else:
            vals['state_id'] = False

        return {'value': vals}

    def create_voucher_move_line(self, cr, uid, retention, voucher, context=None):

        voucher_obj = self.pool.get('account.voucher')

        move_lines = []

        if retention.amount == 0.0:
            return move_lines

        company_currency = voucher.company_id.currency_id.id
        current_currency = voucher.currency_id.id

        tax_amount_in_company_currency =  voucher_obj._convert_paid_amount_in_company_currency(cr, uid, voucher, retention.amount, context=context)
        base_amount_in_company_currency =  voucher_obj._convert_paid_amount_in_company_currency(cr, uid, voucher, retention.base, context=context)

        debit = credit = 0.0

        debit = credit = 0.0
        if voucher.type in ('purchase', 'payment'):
            credit = tax_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = tax_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1

        # Creamos la linea contable perteneciente a la retencion
        move_line = {
            'name': retention.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': retention.account_id.id,
            'tax_code_id': retention.tax_code_id.id,
            'tax_amount': tax_amount_in_company_currency,
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': company_currency <> current_currency and  current_currency or False,
            'amount_currency': company_currency <> current_currency and sign * retention.amount or 0.0,
            'date': voucher.date,
            'date_maturity': voucher.date_due
        }

        move_lines.append(move_line)

        # ...y ahora creamos la linea contable perteneciente a la base imponible de la retencion
        # Notar que credit & debit son 0.0 ambas. Lo que cuenta es el tax_code_id y el tax_amount
        move_line = {
            'name': retention.name + '(Base Imp)',
            'ref': voucher.name,
            'debit': 0.0,
            'credit': 0.0,
            'account_id': retention.account_id.id,
            'tax_code_id': retention.base_code_id.id,
            'tax_amount': base_amount_in_company_currency,
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': False,
            'amount_currency': 0.0,
            'date': voucher.date,
            'date_maturity': voucher.date_due
        }

        move_lines.append(move_line)
        return move_lines

retention_tax_line()


class account_voucher(osv.osv):

    _name = 'account.voucher'

    _inherit = 'account.voucher'

    _columns = {

        'retention_ids': fields.one2many('retention.tax.line', 'voucher_id', 'Retentions', readonly=True, states={'draft':[('readonly', False)]}),

    }


    def cancel_voucher(self, cr, uid, ids, context=None):

        for voucher in self.browse(cr, uid, ids, context=context):

            if voucher.type == 'payment':

                for ret in voucher.retention_ids:

                    if ret.certificate_no:

                        raise osv.except_osv('UserError', 'You cant cancel a voucher with retention')

        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)



    def _get_retention_amount(self, retention_ids):

        amount = 0.0

        for retention in retention_ids:

            amount += retention.amount

        return amount

    @api.onchange('payment_line_ids', 'issued_check_ids', 'third_check_ids', 'retention_ids')
    def onchange_payment_line(self):

        super(account_voucher, self).onchange_payment_line()

        self.amount += self._get_retention_amount(self.retention_ids)

    @api.onchange('third_check_receipt_ids')
    def onchange_third_receipt_checks(self):

        super(account_voucher, self).onchange_third_receipt_checks()

        self.amount += self._get_retention_amount(self.retention_ids)

    def create_move_line_hook(self, cr, uid, voucher_id, move_id, move_lines, context={}):
        retention_line_obj = self.pool.get("retention.tax.line")
        move_lines = super(account_voucher, self).create_move_line_hook(cr, uid, voucher_id, move_id, move_lines, context=context)
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)

        for ret in voucher.retention_ids:

            ret_vals = {}

            if voucher.type == 'payment':

                if not ret.certificate_no:

                    retention_type = self.pool.get('retention.retention').browse(cr, uid, ret.retention_id.id ).type

                    if retention_type == 'profit':

                        ret_vals['certificate_no'] = self.pool.get('ir.sequence').get(cr, uid, 'rtl.profit.seq')

                    if retention_type == 'vat':

                        ret_vals['certificate_no'] = self.pool.get('ir.sequence').get(cr, uid, 'rtl.vat.seq')

                    if retention_type == 'gross_income':

                        ret_vals['certificate_no'] = self.pool.get('ir.sequence').get(cr, uid, 'rtl.gross.seq')

            else:

                if not ret.certificate_no:

                    raise osv.except_osv(_('Retention Error!'),
                            _('Retention without certificate number.'))

            date = ret.date

            if not ret.date:

                date = voucher.date

            res = retention_line_obj.create_voucher_move_line(cr, uid, ret, voucher, context=context)
            if res:
                res[0]['move_id'] = move_id
                res[1]['move_id'] = move_id
                move_lines.append(res[0])
                move_lines.append(res[1])

            # Escribimos valores del voucher en la retention tax line
            ret_vals['voucher_number'] = voucher.number
            ret_vals['partner_id'] = voucher.partner_id.id
            ret_vals['date'] = date


            retention_line_obj.write(cr, uid, ret.id, ret_vals, context=context)

        return move_lines

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
