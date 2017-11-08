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


class RetentionPartnerRule(models.Model):
    _name = 'retention.partner.rule'
    _description = 'Reglas Retenciones Terceros'

    @api.one
    @api.constrains('retention_id','activity_id')
    def _check_activity(self):
        if self.activity_id and self.retention_id.type != 'profit':
            raise Warning("Para las retenciones de tipo {} no se debe configurar actividad".format(self.retention_id.name))
        elif not self.activity_id and self.retention_id.type == 'profit':
            raise Warning("Para las retenciones de tipo {} se debe configurar actividad".format(self.retention_id.name))

    @api.one
    @api.constrains('percentage','retention_id')
    def _check_percentage(self):
        if self.percentage and self.retention_id.type == 'profit':
            raise Warning("Para las retenciones de tipo {} el porcentaje debe ser 0 ".format(self.retention_id.name))

    @api.onchange('retention_id')
    def onchange_ret(self):
        domain = {}
        if self.retention_id.retention_rule_ids:
            activity_ids = []
            for r in self.retention_id.retention_rule_ids:
                activity_ids.append(r.activity_id.id)
            domain['activity_id'] = [('id', 'in', activity_ids)]
        return {'domain': domain}

    activity_id = fields.Many2one(
        comodel_name='retention.activity',
        string="Actividad",
    )

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        ondelete="cascade",
    )

    retention_id = fields.Many2one(
        comodel_name='retention.retention',
        string='Retencion',
        required=True,
        domain="[('type_tax_use','=','purchase')]",
    )

    percentage = fields.Float(
        string='Porcentaje',
        required=True,
    )

    type = fields.Selection(
        selection=[
            ('vat', 'IVA'),
            ('gross_income', 'Ingresos Brutos'),
            ('profit', 'Ganancias'),
            ('other', 'Otro'),
        ],
        string="Tipo",
        related='retention_id.type',
        store=True,
        readonly=True,
    )

    state_id = fields.Many2one(
        'res.country.state',
        string="Provincia",
        related='retention_id.state_id',
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Empresa',
        required=True,
        readonly=True,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('retention.partner.rule'),
    )

    _sql_constraints = [
        ('retention_partner_rule_uniq', 'unique(partner_id,retention_id,activity_id)', 'The rule already exist!')
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
