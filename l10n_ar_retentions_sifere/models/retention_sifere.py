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
import base64

from openerp import models, fields


class RetentionSifere(models.Model):
    _name = 'retention.sifere'

    def generate_file(self):

        buffer_string = ' '

        self.file = base64.encodestring(buffer_string)
        self.filename = 'ret_iibb_{}_{}.txt'.format(
            str(self.date_from).replace('-', ''),
            str(self.date_to).replace('-', ''),
        )

    name = fields.Char(string='Nombre', required=True)

    date_from = fields.Date(string='Desde', required=True)

    date_to = fields.Date(string='Hasta', required=True)

    file = fields.Binary(string='Archivo', filename="filename")

    filename = fields.Char(string='Nombre Archivo')

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('retention.sifere')
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
