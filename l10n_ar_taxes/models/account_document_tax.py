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


class AccountDocumentTax(models.AbstractModel):
    _name = 'account.document.tax'

    currency_id = fields.Many2one('res.currency')
    amount = fields.Monetary('Importe', currency_field='currency_id', required=True)
    base = fields.Monetary('Base', currency_field='currency_id')
    jurisdiction = fields.Selection(
        [
            ('nacional', 'Nacional'),
            ('provincial', 'Provincial'),
            ('municipal', 'Municipal')
        ],
        string='Jurisdiccion',
        required=True,
    )
    name = fields.Char('Nombre', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Compania',
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('amount')
    def check_amount(self):
        for tax in self:
            if tax.amount <= 0:
                raise ValidationError('El monto del impuesto debe ser mayor a 0')

    @api.constrains('base')
    def check_base(self):
        for tax in self:
            if tax.base < 0:
                raise ValidationError('La base del impuesto no puede ser negativa')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
