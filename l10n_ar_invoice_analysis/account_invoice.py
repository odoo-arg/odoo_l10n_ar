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

class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    amount_untaxed_analysis = fields.Float('Subtotal', compute='_get_amount_untaxed_analysis', store=True)
    amount_total_analysis = fields.Float('Total', compute='_get_amount_total_analysis', store=True)
    residual_analysis = fields.Float('Balance', compute='_get_residual_analysis', store=True)
    type_analysis = fields.Selection([('fc','FC'),('nc','NC'),('nd','ND')], string="Tipo doc.", store=True, compute='_get_type_analysis')


    @api.one
    @api.depends('type', 'is_debit_note')
    def _get_type_analysis(self):

        if self.type in ('in_refund', 'out_refund'):

            self.type_analysis = 'nc'

        else:

            self.type_analysis = 'nd' if self.is_debit_note else 'fc'

    @api.one
    @api.depends('amount_untaxed')
    def _get_amount_untaxed_analysis(self):

        self.read(['amount_untaxed'])
        self.amount_untaxed_analysis = -self.amount_untaxed if self.type in ('out_refund', 'in_refund') else self.amount_untaxed

    @api.one
    @api.depends('amount_total')
    def _get_amount_total_analysis(self):

        self.read(['amount_total'])
        self.amount_total_analysis = -self.amount_total if self.type in ('out_refund', 'in_refund') else self.amount_total

    @api.one
    @api.depends('residual')
    def _get_residual_analysis(self):

        self.read(['residual'])
        self.residual_analysis = -self.residual if self.type in ('out_refund', 'in_refund') else self.residual


AccountInvoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
