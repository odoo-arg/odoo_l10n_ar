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
    def onchange_type_tax_use_domain(self):
        domain = {}
        domain['tax_id'] = [('type_tax_use', '=', self.type_tax_use), ('tax_group_id', '=', self.env.ref('l10n_ar_retentions.tax_group_retention').id)]
        return {'domain': domain }

    def get_domain(self):
        return [('type_tax_use', '=', self.type_tax_use), ('tax_group_id', '=', self.env.ref('l10n_ar_retentions.tax_group_retention').id)]

    tax_id = fields.Many2one(
        domain=get_domain,
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
