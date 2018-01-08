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


class AccountFiscalPosition(models.Model):

    _inherit = 'account.fiscal.position'

    denomination_fiscal_position_ids = fields.One2many(
        'denomination.fiscal.position',
        'issue_fiscal_position_id',
        'Denominaciones y posiciones fiscales',
        help="Desde aqui se realizan los mapeos para ver que tipo de documento se realizan"
             " a otras posiciones fiscales\npara cada denominacion"
    )

    @api.constrains('denomination_fiscal_position_ids')
    def _check_position_fiscal(self):
        fiscal_positions = self.env['denomination.fiscal.position'].search([
            ('issue_fiscal_position_id', '=', self.id)
        ])
        denomination_count = len(fiscal_positions.mapped('receipt_fiscal_position_id'))
        if len(fiscal_positions) != denomination_count:
            raise ValidationError("No se pueden repetir posiciones fiscales en el mapeo de denominaciones.")

    def get_denomination(self, receipt_fiscal_position):
        """
        Busca la denominacion para la posicion fiscal que se pide
        :param receipt_fiscal_position: account.fiscal.position - Posicion fiscal receptora
        :return: account.denomination - Denominacion resultante
        :raise: ValidationError - No esta configurada la denominacion para ese caso
        """

        denomination_fiscal_position = self.denomination_fiscal_position_ids.filtered(
            lambda x: x.receipt_fiscal_position_id == receipt_fiscal_position
        )

        if not denomination_fiscal_position:
            raise ValidationError('No se encuentra configurada una denominacion para las posiciones fiscales:\n'
                                  + self.name + ' - ' + receipt_fiscal_position.name)

        return denomination_fiscal_position.account_denomination_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
