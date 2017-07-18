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


class DocumentBook(models.Model):

    _name = 'document.book'

    name = fields.Char('Ultimo numero', required=True, size=8)
    pos_ar_id = fields.Many2one('pos.ar', 'Punto de venta', required=True)
    category = fields.Selection([
        ('invoice', 'Factura'),
        ('payment', 'Recibo'),
        ('picking', 'Remito')],
        'Categoria',
        required=True
    )
    book_type_id = fields.Many2one('document.book.type', 'Tipo de talonario', required=True)
    document_type_id = fields.Many2one(
        'document.book.document.type',
        'Tipo de documento',
        help="En los casos qe se utilice el mismo punto de venta para distintos documentos\n"
             "Por ejemplo, facturas y notas de credito/debito"
    )
    denomination_id = fields.Many2one('account.denomination', 'Denominacion', required=True)
    sequence = fields.Integer('Secuencia', help='Por default, se eligirá el que menos secuencia tiene')

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
        name_list = super(DocumentBook, self).name_get()
        for name in name_list:
            name_get.append((name[0], name[1].zfill(8)))
        return name_get


    _sql_constraints = [
        ('denomination_pos_ar_unique', 'unique(document_type_id, denomination_id, pos_ar_id, category)',
         'El talonario debe ser unico por la combinacion punto de venta/denominacion/categoria/tipo de documento'),
        ('sequence_uniq', 'unique(category, sequence, document_type_id)', 'La secuencia debe ser unica por categoria')
    ]

    def next_number(self):
        """
        Suma uno al ultimo valor del talonario y lo devuelve
        :return: Numero para ser utilizado
        """
        self.name = int(self.name) + 1
        return self.pos_ar_id.name.zfill(4) + '-' + self.name.zfill(8)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
