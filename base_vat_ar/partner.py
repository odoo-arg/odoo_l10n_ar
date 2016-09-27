# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp.osv import osv, fields
from openerp.tools.translate import _

class res_document_type(osv.osv):

    _name = 'res.document.type'

    _description = 'Document type'

    _columns = {

        'name': fields.char('Document type', size=40),
        'afip_code': fields.char('Afip code', size=10),
        'verification_required': fields.boolean('Verification required'),
        'company_id': fields.many2one('res.company', 'Company', required=True),

    }

    _defaults = {

        'verification_required': lambda *a: False,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'res.document.type'),


    }

res_document_type()


class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {

        'document_type_id': fields.many2one('res.document.type', 'Document type'),

    }

    def exist_vat (self, cr, uid, ids, context=None):

        for partner in self.browse(cr, uid, ids, context=context):

            if partner.vat and partner.document_type_id and partner.is_company:

                cr.execute("""SELECT 1 FROM res_partner WHERE vat = %s AND document_type_id = %s AND is_company AND id <> %s""" , (partner.vat, partner.document_type_id.id, partner.id) )

                vat_repetido = cr.fetchall()

                if vat_repetido:

                    return False

        return True


    def check_vat(self, cr, uid, ids, context=None):

        for partner in self.browse(cr, uid, ids, context=context):
            if not partner.vat:
                continue
            if partner.parent_id:
                continue
            if partner.country_id:
                vat_country = partner.country_id.code.lower()
                vat_number = partner.vat
            else:
                vat_country, vat_number = partner.vat[:2].lower(), partner.vat[2:].replace(' ', '')

            if partner.document_type_id and partner.document_type_id.verification_required:

                if not hasattr(self, 'check_vat_' + vat_country):
                    return False

                check = getattr(self, 'check_vat_' + vat_country)
                if not check(vat_number):
                    return False
        return True


    def check_vat_ar(self,vat):

        print "chequeando CUIT de Argentina...."
        if len(vat) != 11: return False
        try:
            int(vat)
        except ValueError:
            return False

        l=[5,4,3,2,7,6,5,4,3,2]

        var1=0
        for i in range(10):
            var1=var1+int(vat[i])*l[i]
        var3=11-var1%11

        if var3==11: var3=0
        if var3==10: var3=9
        if var3 == int(vat[10]):

            return True

        return False


    _constraints = [

        (check_vat, _('The Vat does not seems to be correct.'), ['vat']) ,
        (exist_vat, _('That Vat already exist for other partner.'), ['vat', 'is_company']),

    ]

res_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
