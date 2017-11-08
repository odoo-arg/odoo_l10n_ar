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


class RetentionRetention(models.Model):
    _inherit = 'retention.retention'

    @api.one
    @api.constrains('retention_rule_ids')
    def _check_rules(self):
        if self.type_tax_use == 'purchase' and self.type == 'gross_income' and len(self.retention_rule_ids) > 1:
            raise Warning("Para este tipo de retencion solo debe existir una regla")

    retention_rule_ids = fields.One2many(
        comodel_name='retention.retention.rule',
        inverse_name='retention_id',
        string="Reglas Retenciones"
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
