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
from openerp.exceptions import ValidationError


class WizardSellCheck(models.TransientModel):

    _name = "wizard.sell.check"

    def _get_default_initial_amount(self):

        active_ids = self.env.context.get('active_ids')
        amount = sum(check.amount for check in self.env['account.third.check'].browse(active_ids))

        return amount

    @api.depends('commission', 'interests', 'initial_amount')
    def _compute_amount(self):
        self.amount = self.initial_amount - self.interests - self.commission

    bank_account_id = fields.Many2one(
        'account.journal',
        'Cuenta bancaria',
        domain=[('type', '=', 'bank')],

    )
    partner_id = fields.Many2one('res.partner', 'Partner')
    journal_id = fields.Many2one(
        'account.journal',
        'Diario',
        domain=[('type', 'in', ('cash', 'bank'))],
    )
    account_id = fields.Many2one(
        'account.account',
        'Cuenta para la acreditacion del dinero',
        required=True
    )
    date = fields.Date(
        'Fecha de la operacion',
        required=True
    )
    commission = fields.Float(
        'Importe de la comision'
    )
    interests = fields.Float(
        'Importe de los intereses'
    )
    initial_amount = fields.Float(
        'Importe inicial',
        default=_get_default_initial_amount
    )
    amount = fields.Float(
        'Total a cobrar',
        compute='_compute_amount',
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Compania',
        default=lambda self: self.env['res.company']._company_default_get('wizard.sell.check'),
    )
    commission_account_id = fields.Many2one(
        'account.account',
        'Cuenta para las comisiones',
    )
    interest_account_id = fields.Many2one(
        'account.account',
        'Cuenta para los intereses'
    )

    @api.constrains('interests', 'commission')
    def constrain_amount(self):
        if self.interests < 0 or self.commission < 0 or self.amount < 0:
            raise ValidationError("Los importes no pueden ser negativos")

    def create_sold_check_document(self):
        """ Crea un documento de cheques vendidos y devuelte su vista formulario """
        third_check_proxy = self.env['account.third.check']
        active_ids = self.env.context.get('active_ids')
        checks = third_check_proxy.browse(active_ids)

        self._check_fields(checks)
        sold_check = self._create_sold_check(checks)
        view = self._get_sold_check_view(sold_check)

        return view

    def _create_sold_check(self, checks):
        """
        Crea un account.sold.check
        :param checks: accoount.third.check que se asociaran a la venta de cheques
        """
        return self.env['account.sold.check'].create({
            'date': self.date,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'bank_account_id': self.bank_account_id.id,
            'commission_account_id': self.commission_account_id.id,
            'interest_account_id': self.interest_account_id.id,
            'account_id': self.account_id.id,
            'commission': self.commission,
            'interests': self.interests,
            'account_third_check_ids': [(6, 0, checks.ids)],
        })

    def _get_sold_check_view(self, sold_check):
        """
        Devuelve la vista form de cheques vendido
        :param sold_check: account.sold.check del cual se devolvera la vista
        """
        return {
            'name': 'Cheques vendidos',
            'views': [[False, "form"]],
            'res_model': 'account.sold.check',
            'type': 'ir.actions.act_window',
            'res_id': sold_check.id,
        }

    def _check_fields(self, checks):
        """ Valida que los cheques tengan la información necesaria para ser vendidos """
        for check in checks:
            if check.state != 'wallet':
                raise ValidationError("Los cheques seleccionados deben estar en cartera. "
                                      "\n El cheque {} no esta en cartera".format(check.name))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
