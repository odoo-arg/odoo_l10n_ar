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

from openerp import models, fields, api, _

class perception_perception(models.Model):

    """Objeto que define las percepciones que pueden utilizarse
       Configura las percepciones posibles. Luego a partir de estos objetos
       se crean perception.tax que iran en las account.invoice.
       Además, se crean account_invoice_tax que serian percepciones que se realizan en ;
       una factura, ya sea, de proveedor o de cliente. Y a partir de estas se
       crean los asientos correspondientes.
       De este objeto se toma la configuracion para generar las perception.tax y
       las account.invoice.tax con datos como monto, base imponible,
       nro de certificado, etc."""

    _name = "perception.perception"

    _description = "Perception Configuration"

    name = fields.Char(string='Perception', required=True, size=64)
    tax_id = fields.Many2one('account.tax', string='Tax', required=True, help="Tax configuration for this perception")
    type_tax_use = fields.Selection(related= 'tax_id.type_tax_use', string='Tax Application', readonly=True)
    state_id = fields.Many2one('res.country.state', string='State/Province')
    afip_code = fields.Char(string='Afip Code',)

    type = fields.Selection([('vat', 'VAT'),
                              ('gross_income', 'Gross Income'),
                              ('profit', 'Profit'),
                              ('other', 'Other')], 'Type', default='vat')

    jurisdiccion = fields.Selection([('nacional', 'Nacional'),
                                      ('provincial', 'Provincial'),
                                      ('municipal', 'Municipal')], string='Jurisdiccion', default='nacional')

    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=True,
                                 readonly=True,
                                 change_default=True,
                                 default=lambda self: self.env['res.company']._company_default_get('perception.perception')
                                )

perception_perception()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

