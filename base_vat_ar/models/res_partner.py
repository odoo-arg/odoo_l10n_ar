# -*- encoding: utf-8 -*-
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from odoo_openpyme_api.padron import contributor

class ResPartner(models.Model):

    _inherit = 'res.partner'

    partner_document_type_id = fields.Many2one('partner.document.type', 'Tipo de documento')
     
    @api.constrains("vat", "partner_document_type_id")
    def check_vat(self):
           
        #Si la empresa tiene el mismo pais, obviamos la parte de que el documento
        #necesite el prefijo del pais adelante para el chequeo de documento
        if self.country_id.no_prefix:
            check_func = self.simple_vat_check
            if not check_func(self.country_id.code.lower(), self.vat):
                raise ValidationError("El numero de documento [{vat}] no parece ser correcto para el tipo [{type}]".format(
                        vat=self.vat, 
                        type=self.partner_document_type_id.name
                    )
                )
        else:
            super(ResPartner, self).check_vat()

    def check_vat_ar(self, vat_number):
        ''' Verifica que el numero de documento sea correcto para su posicion fiscal '''
        
        if vat_number and self.partner_document_type_id.verification_required:
            return contributor.Contributor.is_valid_cuit(vat_number)
        
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: