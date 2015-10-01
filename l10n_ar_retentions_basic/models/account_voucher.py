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

from openerp import models, fields, api
from openerp.exceptions import Warning

import logging
_logger = logging.getLogger(__name__)


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    retention_ids = fields.One2many(
        'retention.tax.line',
        'voucher_id',
        string='Retenciones',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    @api.multi
    def cancel_voucher(self):

        for voucher in self:

            if voucher.type == 'payment':

                for ret in voucher.retention_ids:

                    if ret.certificate_no:

                        raise Warning('No se puede cancelar un recibo con retenciones')

        return super(AccountVoucher, self).cancel_voucher()


    @api.multi
    def _get_retention_amount(self):

        amount = 0.0

        for retention in self.retention_ids:

            amount += retention.amount

        return amount


    @api.onchange('payment_line_ids', 'issued_check_ids', 'third_check_ids', 'retention_ids')
    def onchange_payment_line(self):

        super(AccountVoucher, self).onchange_payment_line()

        self.amount += self._get_retention_amount()

    @api.onchange('third_check_receipt_ids')
    def onchange_third_receipt_checks(self):

        super(AccountVoucher, self).onchange_third_receipt_checks()

        self.amount += self._get_retention_amount()


    def create_move_line_hook(self, cr, uid, voucher_id, move_id, move_lines, context={}):

        retention_line_obj = self.pool.get("retention.tax.line")

        move_lines = super(AccountVoucher, self).create_move_line_hook(cr, uid, voucher_id, move_id, move_lines, context=context)

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

                    raise Warning('Retencion sin numero de certificado.')


            if not ret.date:

                date = voucher.date

            else:

                date = ret.date

            res = retention_line_obj.create_voucher_move_line(cr, uid, ret, voucher, context=context)

            res['move_id'] = move_id
            move_lines.append(res)

            ret_vals['date'] = date

            retention_line_obj.write(cr, uid, ret.id, ret_vals, context=context)

        return move_lines


AccountVoucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
