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


class WsfeConfiguration(models.Model):

    _name = 'wsfe.configuration'

    name = fields.Char('Nombre', required=True)
    type = fields.Selection([
            ('homologation', 'Homologacion'),
            ('production', 'Produccion')
        ],
        'Tipo',
        required=True
    )
    wsaa_configuration_id = fields.Many2one('wsaa.configuration', 'WSAA', required=True)
    # Me parece mal que no este filtrado el token de acceso solo para los de tipo FE. Como por el momento
    # no utilizamos otro lo dejamos asi, tener en cuenta si algun dia se utiliza el wsaa para otros servicios.
    wsaa_token_id = fields.Many2one('wsaa.token', 'Token Acceso', required=True)

    company_id = fields.Many2one(
        'res.company',
        'Empresa',
        required=True,
        default=lambda self: self.env.user.company_id
    )

    _sql_constraints = [('unique_name', 'unique(name)', 'Ya existe una configuracion con ese nombre')]

    @api.constrains('wsaa_token_id')
    def check_unique_ticket(self):
        for wsfe in self:
            if wsfe.search_count([('wsaa_token_id', '=', wsfe.wsaa_token_id.id)]) > 1:
                raise ValidationError('Ya existe una configuracion de factura electronica asociado a ese token')

    @api.onchange('wsaa_configuration_id')
    def onchange_wsaa_configuration(self):
        self.wsaa_token_id = None

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
