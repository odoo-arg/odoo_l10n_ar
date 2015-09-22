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


class invoice_denomination(osv.osv):

    _name = "invoice.denomination"

    _description = "Denomination for Invoices"

    _columns = {

        'company_id': fields.many2one('res.company', 'Company', required=True),
        'name' : fields.char('Denomination', required=True, size=4),
        'desc' : fields.char('Description', required=True, size=100),
        'vat_discriminated' : fields.boolean('Vat Discriminated in Invoices', help="If True, the vat will be discriminated at invoice report."),

    }

    _sql_constraints = [

        ('code_denomination_uniq', 'unique (name)', 'The Denomination of the Invoices must be unique per company !')

    ]

    _defaults = {

        'vat_discriminated': False,
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='pos.ar',context=ctx),

    }

invoice_denomination()


class pos_ar(osv.osv):

    _name = "pos.ar"

    _description = "Point of Sale for Argentina"

    _columns = {

        'company_id': fields.many2one('res.company', 'Company', required=True),
        'name' : fields.char('Nro', required=True, size=6),
        'desc' : fields.char('Description', required=False, size=180),
        'priority' : fields.integer('Priority', required=True, size=6),
        'warehouse_id': fields.many2one('stock.warehouse', 'Warehouse', required=True),        
        'denomination_id': fields.many2one('invoice.denomination', 'Denomination'),
        'print_type': fields.selection( ([('preprinted','Preimpreso'),('electronic_invoice','Factura Electronica'),('fiscal_printer','Impresora Fiscal')]),required=True,),

    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        if not ids:
            return []
        for id in ids:
            if not id:
                continue
            reads = self.read(cr, uid, [id], ['name', 'denomination_id'], context=context)
            for record in reads:
                name = record['name']
                if record['denomination_id']:
                    name = record['denomination_id'][1] + ' '+ name
                res.append((record['id'], name))
        return res

    _defaults = {

        'print_type': lambda *args: 'preprinted',
        'company_id': lambda self,cr,uid,ctx: self.pool['res.company']._company_default_get(cr,uid,object='pos.ar',context=ctx),

    }

pos_ar()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
