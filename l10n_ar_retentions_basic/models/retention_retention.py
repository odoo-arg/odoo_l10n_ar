# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from openerp.exceptions import Warning

class RetentionRetention(models.Model):

    _name = "retention.retention"

    _description = "Retention"

    name = fields.Char(string="Nombre", required=True)

    tax_id = fields.Many2one("account.tax", string="Impuesto", required=True, domain=[('tax_group','=','retention')])

    type_tax_use = fields.Selection(related="tax_id.type_tax_use", string="Aplica para", readonly=True,)

    type = fields.Selection([('vat','IVA'),('gross_income','Ingresos Brutos'),('profit','Ganancias'),('other','Otro')], string="Tipo", required=True, default="vat")

    jurisdiccion = fields.Selection([('nacional','Nacional'),('provincial','Provincial'),('municipal','Municipal')], string="Jurisdiccion", required=True, default="nacional")

    state_id = fields.Many2one("res.country.state", string="Provincia",)

    afip_code = fields.Char(string="Codigo Afip")

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        readonly=True,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('retention.retention')
    )

RetentionRetention()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
