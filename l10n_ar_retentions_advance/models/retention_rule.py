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


class RetentionRetentionRule(models.Model):
    _name = 'retention.retention.rule'
    _description = 'Regla de retencion'

    @api.one
    @api.constrains('retention_id','activity_id')
    def _check_activity(self):
        if self.activity_id and self.retention_id.type != 'profit':
            raise Warning("Para las retenciones de tipo {} no se debe configurar actividad".format(self.retention_id.name))
        elif not self.activity_id and self.retention_id.type == 'profit':
            raise Warning("Para las retenciones de tipo {} se debe configurar actividad".format(self.retention_id.name))

    retention_id = fields.Many2one(
        comodel_name='retention.retention',
        string="Retencion",
        ondelete='cascade',
    )

    activity_id = fields.Many2one(
        comodel_name='retention.activity',
        string="Actividad",
    )

    not_applicable_minimum = fields.Float(
        string='Minimo no imponible',
        required=True,
    )

    minimum_tax = fields.Float(
        string='Impuesto Minimo',
        required=True,
    )

    percentage = fields.Float(
        string='Porcentaje',
        required=True,
    )

    exclude_minimum = fields.Boolean(
        string='Excluir Minimo',
        default=False,
    )

    _sql_constraints = [
        ('retention_rule_uniq', 'unique(retention_id,activity_id)', 'Ya existe una regla para esta retencion y actividad')
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
