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

from openerp.osv import osv
from openerp.tools.translate import _

class stock_picking(osv.osv):

    _inherit = "stock.picking"

    #overwrite
    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='out_invoice', context=None):

        invoice_ids = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id, group, type, context)

        invoice_obj = self.pool.get('account.invoice')

        for picking in self.browse(cr, uid, ids, context=context):

            denom_id = False
            res_pos = False
            order_to_pick = False

            if picking.sale_id and picking.sale_id.invoice_ids:

                for inv in picking.sale_id.invoice_ids:

                    if inv.id in invoice_ids:

                        order_to_pick = picking.sale_id

                        if not order_to_pick.fiscal_position :
                            raise osv.except_osv( _('Error'),
                                                  _('Check the Fiscal Position Configuration'))

                        denom_id = order_to_pick.fiscal_position.denomination_id

                        pos_ar_obj = self.pool.get('pos.ar')

                        res_pos = pos_ar_obj.search(cr, uid,[('warehouse_id', '=', order_to_pick.warehouse_id.id), ('denomination_id', '=', denom_id.id)])

                        if not res_pos:
                            raise osv.except_osv(_('Error'),
                                                 _('No hay punto de venta para este deposito.'))

                        vals = {'denomination_id' : denom_id.id , 'pos_ar_id': res_pos[0] }

                        inv.write(vals)

        return invoice_ids

stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
