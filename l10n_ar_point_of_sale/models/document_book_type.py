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


class DocumentBookType(models.Model):

    _name = 'document.book.type'

    def _get_name(self):
        for book in self:
            # Obtenemos el valor del nombre del campo seleccion para la categoria
            selection_value = dict(book.fields_get()['type']['selection'])[book.type]
            book.name = selection_value

    name = fields.Char('Nombre', compute='_get_name')
    type = fields.Selection([('preprint', 'Preimpreso')], 'Tipo', required=True)
    category = fields.Selection([
        ('invoice', 'Factura'),
        ('payment', 'Pago'),
        ('picking', 'Remito')],
        'Categoria',
        required=True
    )
    foo = fields.Char('Funcion', help='Funcion a ejecutarse al utilizar tipo de talonario')

    _sql_constraints = [(
        'unique_name_categ',
        'unique(name, category)',
        'Ya existe ese tipo de talonario para esa categoría'
    )]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
