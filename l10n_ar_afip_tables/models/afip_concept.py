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

from openerp import models, fields

product_concept_selection = [
    ('consu', 'Consumible'),
    ('service', 'Service'),
    ('product', 'Almacenable'),
]

class AfipConcept(models.Model):

    _name = 'afip.concept'

    name = fields.Char('Nombre', required=True)
    product_concept_ids = fields.Many2many(
        'product.concept.category', 
        string='Categoria de conceptos'
    )
    
class ProductConcept(models.Model):

    _name = 'product.concept'

    name = fields.Char('Descripcion', required=True)
    type = fields.Selection(
        string='Tipo', 
        selection=product_concept_selection,
        required=True
    )
    product_concept_category_id = fields.Many2one(
        'product.concept.category', 
        'Categoria de concepto', 
        required=True
    )
    
class ProductConceptCategory(models.Model):

    _name = 'product.concept.category'
    
    name = fields.Char('Nombre', required=True)
    afip_concept_ids = fields.Many2many('afip.concept', string='Concepto Afip')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: