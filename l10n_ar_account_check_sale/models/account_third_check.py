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


class AccountThirdCheck(models.Model):

    _inherit = 'account.third.check'

    @api.depends('sold_check_ids')
    def get_sold_check_id(self):
        for check in self:
            check.sold_check_id = check.sold_check_ids[0].id\
                if check.sold_check_ids else None

    sold_check_ids = fields.Many2many(
        'account.sold.check',
        'third_check_sold_check_rel',
        'third_check_id',
        'sold_check_id',
        string='Documentos de venta de cheques'
    )
    sold_check_id = fields.Many2one(
        'account.sold.check',
        'Documento de venta',
        compute='get_sold_check_id',
    )
    sold_bank_id = fields.Many2one(
        'account.journal',
        'Cuenta bancaria de venta',
        related='sold_check_id.bank_account_id',
        readonly=True
    )
    sold_partner_id = fields.Many2one(
        'res.partner',
        'Vendido a',
        related='sold_check_id.partner_id',
        readonly=True
    )
    sold_date = fields.Date(
        'Fecha de venta',
        related='sold_check_id.date',
        readonly=True
    )

    @api.constrains('sold_check_ids')
    def sold_check_contraints(self):
        if any(check.state != 'wallet' for check in self):
            raise ValidationError('Solo se puede modificar el documento de venta de un cheque en cartera.')
        for check in self:
            if len(check.sold_check_ids) > 1:
                raise ValidationError("El cheque {} ya se encuentra en un documento de venta".format(check.name))

    @api.multi
    def post_sold_check(self):
        if any(check.state != 'wallet' for check in self):
            raise ValidationError("Todos los cheques a vender deben estar en cartera")
        if len(self.mapped('currency_id')) > 1:
            raise ValidationError("No se pueden depositar cheques de distintas monedas en la misma boleta de deposito")
        self.next_state('wallet_sold')

    @api.multi
    def cancel_sold_check(self):
        if any(check.state not in ('sold', 'wallet') for check in self):
            raise ValidationError("Para cancelar el documento de venta de cheques"
                                  " los cheques deben estar depositados o en cartera")
        self.cancel_state('sold')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
