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
from openerp.exceptions import ValidationError


class DocumentBook(models.Model):
    _inherit = 'document.book'

    def action_wsfe_number(self, afip_wsfe, document_afip_code):
        """
        Valida que el ultimo numero del talonario sea el correcto en comparacion con el de la AFIP.
        :param afip_wsfe: instancia Wsfe.
        :param document_afip_code: Codigo de afip del documento.
        """
        last_number = str(afip_wsfe.get_last_number(self.pos_ar_id.name, document_afip_code))

        if last_number.zfill(8) != self.name.zfill(8):
            raise ValidationError('El ultimo numero del talonario ({0}) no coincide con el de la AFIP ({1})'.format(
                self.name, last_number))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
