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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time
import logging
_logger = logging.getLogger(__name__)


class sale_advance_payment_inv(osv.osv_memory):

    _inherit = "sale.advance.payment.inv"

    def _create_invoices(self, cr, uid, inv_values, sale_id, context=None):

        sale = self.pool.get('sale.order').browse(cr, uid, sale_id, context=context)[0]

        if not sale.fiscal_position :
            raise osv.except_osv( _('Error'),_('Revise la posicion fiscal de la orden de venta'))

        denom_id = sale.fiscal_position.denomination_id.id
        warehouse_id = sale.warehouse_id.id

        pos_ids = self.pool.get('pos.ar').search(cr, uid,[('warehouse_id','=',warehouse_id),('denomination_id','=',denom_id)])

        if not len(pos_ids):
            raise osv.except_osv( _('Error'),_('Revise la configuracion de los puntos de venta'))

        inv_values['denomination_id'] = denom_id
        inv_values['pos_ar_id'] = pos_ids[0]

        inv_id = super(sale_advance_payment_inv, self)._create_invoices( cr, uid, inv_values, sale_id, context)

        return inv_id

sale_advance_payment_inv()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
