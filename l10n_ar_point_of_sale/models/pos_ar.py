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


class PosAr(models.Model):

    _name = 'pos.ar'

    name = fields.Char('Nombre', required=True, size=4)
    description = fields.Char('Descripcion')
    document_book_ids = fields.One2many(
        'document.book',
        'pos_ar_id',
        'Talonarios'
    )

    @api.one
    @api.constrains('name')
    def check_name(self):
        try:
            int(self.name)
        except Exception:
            raise ValidationError('El nombre debe contener solo números enteros')

    @api.multi
    def name_get(self):

        name_get = []
        name_list = super(PosAr, self).name_get()
        for name in name_list:
            name_get.append((name[0], name[1].zfill(4)))
        return name_get

    def get_pos(self, category, denomination):
        """
        Busca el punto de venta con mas prioridad para esa categoria y denominacion
        :param category: categoria (invoice, receipt, picking)
        :param denomination: account.denomination
        :return: Punto de venta prioritario
        """
        document_book = self.env['document.book'].search([
            ('category', '=', category),
            ('denomination_id', '=', denomination.id)
        ], order="sequence asc", limit=1)

        if not document_book:
            raise ValidationError('No se encontro un talonario para esa denominacion y categoria\n'
                                  'por favor, configurar uno')

        return document_book.pos_ar_id

    _sql_constraints = [
        ('type_unique', 'unique(name)', 'Ya existe un punto de venta con ese nombre')
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
