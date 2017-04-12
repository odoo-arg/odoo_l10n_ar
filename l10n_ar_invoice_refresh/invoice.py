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


class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def _invoice_refresh(self, cr, uid, ids, context=None):

        pos_obj = self.pool.get('pos.ar')
        fiscal_obj = self.pool.get('account.fiscal.position')

        for invoice in self.browse(cr, uid, context['active_ids'], context):

            denomination_id = False
            pos_ar_id = False

            if invoice.state == 'draft' and invoice.fiscal_position:

                # SUPPLIER INVOICE

                if invoice.type in ['in_invoice', 'in_refund', 'in_debit']:

                    denomination_id = fiscal_obj.browse(cr, uid , invoice.fiscal_position.id).denom_supplier_id.id

                    self.write(cr, uid, invoice.id,{'denomination_id': denomination_id,})

                # CUSTOMER INVOICE
                else:

                    denomination_id = fiscal_obj.browse(cr, uid , invoice.fiscal_position.id).denomination_id.id

                    pos_ar_id = pos_obj.search( cr, uid , [('denomination_id','=',denomination_id)], order='priority asc', limit=1 )

                    if len(pos_ar_id):

                        self.write(cr, uid, invoice.id,{

                            'pos_ar_id': pos_ar_id[0],
                            'denomination_id': denomination_id,

                        })

        return True

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
