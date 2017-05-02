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

from openerp import models, fields, api, _
from openerp.exceptions import Warning


class DocumentBookDocumentType(models.Model):

    _name = 'document.book.document.type'

    name = fields.Char('Nombre', required=True)
    type = fields.Char('Tipo', required=True)
    document_book_type_id = fields.Many2one('document.book.type', 'Tipo de talonario')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
