# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from openerp.osv import osv, fields
from openerp.tools.translate import _
from openerp import workflow
import logging
_logger = logging.getLogger(__name__)

class sale_order_line_make_invoice(osv.osv_memory):

    _name = "sale.order.line.make.invoice"

    _inherit = "sale.order.line.make.invoice"


    #overwrite
    def _prepare_invoice(self, cr, uid, order, lines, context=None):

        res = super(sale_order_line_make_invoice, self)._prepare_invoice( cr, uid, order, lines, context)

        if not order.fiscal_position :
            raise osv.except_osv( _('Error'),
                                  _('Check the Fiscal Position Configuration'))

        denom_id = order.fiscal_position.denomination_id

        pos_ar_obj = self.pool.get('pos.ar')

        pos_ids = pos_ar_obj.search(cr, uid,[('warehouse_id', '=', order.warehouse_id.id), ('denomination_id', '=', denom_id.id)])

        if len(pos_ids):

            res['denomination_id'] = denom_id.id
            res['pos_ar_id'] = pos_ids[0]

        else:

            raise osv.except_osv( _('Error'),
                                  _('Pos for this configuration cannot be found'))

        return res


sale_order_line_make_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
