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
from openerp import netsvc, api
import re
import logging
_logger = logging.getLogger(__name__)

class account_voucher(osv.osv):

    _name = 'account.voucher'

    _inherit = 'account.voucher'

    def _reset_checks_quantity(self, cr, uid, ids, vals, arg, context=None):

        res = {}

        for voucher in ids:

            res[voucher] = 0

        return res

    _columns = {

        'issued_check_ids': fields.one2many('account.issued.check','voucher_id',
                                            'Issued Checks', required=False, copy=False),
        'third_check_receipt_ids': fields.one2many('account.third.check','source_voucher_id',
                                            'Third Checks', required=False, copy=False),
        'third_check_ids': fields.many2many('account.third.check','third_check_voucher_rel',
                                            'dest_voucher_id', 'third_check_id','Third Checks', copy=False),
        'checks_quantity': fields.function(_reset_checks_quantity, 'quantity of checks', type='integer', store=True)
    }


    def _get_issued_checks_amount(self, issued_check_ids):

        amount = 0.0

        for check in issued_check_ids:

            amount += check.amount

        return amount

    def _get_third_checks_amount(self, third_check_ids):

        amount = 0.0

        for check in third_check_ids:

            amount += check.amount

        return amount

    def _get_third_checks_receipt_amount(self, third_check_receipt_ids):

        amount = 0.0

        for check in third_check_receipt_ids:

            amount += check.amount

        return amount

    @api.onchange('third_check_receipt_ids')
    def onchange_third_receipt_checks(self):

        amount = self._get_payment_lines_amount(self.payment_line_ids)
        amount += self._get_third_checks_receipt_amount(self.third_check_receipt_ids)
        checks_quantity = 0

        for checks in self.third_check_receipt_ids:
            if checks.id.__class__.__name__ == 'NewId':

                checks_quantity += 1

        self.checks_quantity = checks_quantity
        self.amount = amount

    @api.onchange('payment_line_ids', 'issued_check_ids', 'third_check_ids')
    def onchange_payment_line(self):

        super(account_voucher, self).onchange_payment_line()

        if self.type in ('receipt'):

            self.amount += self._get_third_checks_receipt_amount(self.third_check_receipt_ids)

        elif self.type in ('payment'):

            self.amount += self._get_third_checks_amount(self.third_check_ids)
            self.amount += self._get_issued_checks_amount(self.issued_check_ids)

    def create_move_line_hook(self, cr, uid, voucher_id, move_id, move_lines, context={}):
        wf_service = netsvc.LocalService('workflow')
        move_lines = super(account_voucher, self).create_move_line_hook(cr, uid, voucher_id, move_id, move_lines, context=context)

        third_check_pool = self.pool.get('account.third.check')
        issued_check_pool = self.pool.get('account.issued.check')

        # Voucher en cuestion que puede ser un Recibo u Orden de Pago
        v = self.browse(cr, uid, voucher_id)

        if v.type in ('sale', 'receipt'):
            for check in v.third_check_receipt_ids:
                if check.amount == 0.0:
                    continue

                res = third_check_pool.create_voucher_move_line(cr, uid, check, v, context=context)
                res['move_id'] = move_id
                move_lines.append(res)
                wf_service.trg_validate(uid, 'account.third.check', check.id, 'draft_cartera', cr)

        elif v.type in ('purchase', 'payment'):
            # Cheques recibidos de terceros que los damos a un proveedor
            for check in v.third_check_ids:
                if check.amount == 0.0:
                    continue

                res = third_check_pool.create_voucher_move_line(cr, uid, check, v, context=context)
                res['move_id'] = move_id
                move_lines.append(res)
                wf_service.trg_validate(uid, 'account.third.check', check.id, 'cartera_delivered', cr)

            # Cheques propios que los damos a un proveedor
            for check in v.issued_check_ids:
                if check.amount == 0.0:
                    continue

                res = issued_check_pool.create_voucher_move_line(cr, uid, check, v, context=context)
                res['move_id'] = move_id
                move_lines.append(res)
                vals = {'issued': True, 'receiving_partner_id': v.partner_id.id}

                if not check.origin:
                    vals['origin'] = v.number

                if not check.issue_date:
                    vals['issue_date'] = v.date
                check.write(vals)

        return move_lines

    #Cambios de estados de los cheques y constraints para cuando se elimina un voucher

    def unlink(self, cr, uid, ids, context=None):

        wf_service = netsvc.LocalService('workflow') 
        third_check_obj = self.pool.get('account.third.check')

        for voucher in self.browse(cr, uid, ids, context=context):

            if voucher.type == 'receipt':

                for check in voucher.third_check_receipt_ids:

                    if ((check.state !='wallet') and (check.state != 'draft')):

                        raise osv.except_osv('UserError', 'You cant delete a voucher with a check that isnt in wallet or draft')

            if voucher.type == 'payment':

                for third_check in voucher.third_check_ids:

                    if (third_check.state != 'delivered'):

                        raise osv.except_osv('UserError', 'You cant delete a voucher with a third check that isnt delivered')

                    wf_service.trg_validate(uid, 'account.third.check', third_check.id, 'delivered_cartera', cr)

                    third_check_obj.write(cr, uid, [third_check.id], {'state': 'wallet'})

                for issued_check in voucher.issued_check_ids:

                    if issued_check.issued:

                        raise osv.except_osv('UserError', 'You cant delete a voucher with an issued check that is issued')

        return super(account_voucher, self).unlink(cr, uid, ids, context=context)


    #Cambios de estados de los cheques y constraints para cuando se cancela un voucher

    def cancel_voucher(self, cr, uid, ids, context=None):

        wf_service = netsvc.LocalService('workflow')

        issued_check_obj = self.pool.get('account.issued.check')
        third_check_obj = self.pool.get('account.third.check')

        for voucher in self.browse(cr, uid, ids, context=context):

            if voucher.type == 'receipt':

                for check in voucher.third_check_receipt_ids:

                    if ((check.state !='wallet') and (check.state != 'draft')):

                        raise osv.except_osv('UserError', 'You cant cancel a voucher with a check that isnt in wallet or draft')

                    wf_service.trg_validate(uid, 'account.third.check', check.id, 'cartera_draft', cr)

                    third_check_obj.write(cr, uid, [check.id], {'state': 'draft'})


            elif voucher.type == 'payment':


                for issued_check in voucher.issued_check_ids:

                    issued_check_obj.write(cr, uid, [issued_check.id], { 'issued': False, 'receiving_partner_id': False, 'origin': False } )


                # Los cheques de terceros vuelven a su estado original previo al pago (La fecha de endoso se borra)

                for third_check in voucher.third_check_ids:

                    if (third_check.state != 'delivered'):

                        raise osv.except_osv('UserError', 'You cant delete a voucher with a third check that isnt delivered')

                    wf_service.trg_validate(uid, 'account.third.check', third_check.id, 'delivered_cartera', cr)

                    third_check_obj.write(cr, uid, [third_check.id], { 'state': 'wallet', 'endorsement_date': False,
                    'destiny_partner_id': False, 'dest': False })


        return super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
