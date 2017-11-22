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


class RetentionRetention(models.Model):
    _inherit = 'account.tax.ar'
    _name = 'retention.retention'

    @api.onchange('type_tax_use')
    def change_tax_id(self):
        self.tax_id = self.env['account.tax'].search(
            [('type_tax_use', '=', self.type_tax_use), ('tax_group_id', '=', self.tax_group_retention_id.id)], limit=1)

    def _get_tax_group_retention(self):
        return self.env.ref('l10n_ar_retentions.tax_group_retention')

    tax_group_retention_id = fields.Many2one(
        comodel_name='account.tax.group',
        default=_get_tax_group_retention,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
