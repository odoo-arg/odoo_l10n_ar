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


class DenominationFiscalPosition(models.Model):
    _name = 'denomination.fiscal.position'

    issue_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        'Posicion Fiscal emisora',
        required=True
    )
    receipt_fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        'Posicion Fiscal receptora',
        required=True
    )
    account_denomination_id = fields.Many2one(
        'account.denomination',
        'Denominacion',
        required=True
    )

    company_id = fields.Many2one('res.company', string='Compania', related='issue_fiscal_position_id.company_id',
                                 store=True, readonly=True, related_sudo=False)

    _sql_constraints = [(
        'unique',
        'unique(issue_fiscal_position_id, receipt_fiscal_position_id, account_denomination_id)',
        'Ya existe esa combinación de posicion fiscal/denominacion'
    )]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
