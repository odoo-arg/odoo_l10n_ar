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

class ResPartner(models.Model):

    _inherit = 'res.partner'

    cuit_country = fields.Selection([('juridica', 'Juridica'), ('fisica', 'Fisica'), ('otro', 'Otra entidad')], string='Tipo de CUIT pais')
    has_country_cuit = fields.Boolean(related='property_account_position.has_country_cuit', string="Tiene CUIT pais")

ResPartner()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: