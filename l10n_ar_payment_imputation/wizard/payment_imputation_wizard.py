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


class PaymentImputationWizard(models.TransientModel):

    _name = 'payment.imputation.wizard'

    @api.depends('payment_imputation_line_ids', 'advance_amount')
    def _get_total_payment(self):
        self.total = sum(imputation.amount for imputation in self.payment_imputation_line_ids)+self.advance_amount

    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id
    )
    payment_type = fields.Selection([('inbound', 'Inbound'), ('outbound', 'Outbound')], 'Tipo')
    advance_amount = fields.Monetary('Importe a cuenta')
    journal_id = fields.Many2one(
        'account.journal',
        domain=[('type', 'in', ('bank', 'cash'))],
        default=lambda self: self.env.ref('l10n_ar_account_payment.journal_cobros_y_pagos'),
        required=True
    )
    payment_imputation_line_ids = fields.Many2many(
        'payment.imputation.line',
        'imputation_payment_wizard_rel',
        'wizard_id',
        'payment_id',
        'Imputaciones',
    )
    total = fields.Monetary('Total', compute=_get_total_payment)
    date = fields.Date('Fecha')

    @api.onchange('payment_type')
    def onchange_type(self):
        partner_type = 'customer' if self.payment_type == 'inbound' else 'supplier'
        return {'domain': {'partner_id': [(partner_type, '=', True)]}}

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        invoice_type = 'out_invoice' if self.payment_type == 'inbound' else 'in_invoice'
        imputation_lines = []
        self.payment_imputation_line_ids = None
        for invoice in self.env['account.invoice'].search([
            ('type', '=', invoice_type),
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'open')
        ]):
            imputation_lines.append((0, 0, {'invoice_id': invoice.id}))

        self.payment_imputation_line_ids = imputation_lines

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.env.user.company_id.currency_id

    def create_payment(self):
        self._validate_payment_imputation()
        payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids \
            or self.journal_id.outbound_payment_method_ids

        payment = self.env['account.payment'].create({
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'payment_type': self.payment_type,
            'partner_type': 'customer' if self.payment_type == 'inbound' else 'supplier',
            'payment_method_id': payment_methods and payment_methods[0].id or False,
            'amount': self.total,
            'payment_imputation_ids': [(4, imputation.id)
                                       for imputation in self.payment_imputation_line_ids.filtered(lambda x: x.amount)],
            'payment_date': self.date or fields.Date.today(),
            'currency_id': self.currency_id.id,
            'advance_amount': self.advance_amount
        })

        return {
            'name': 'Pago',
            'views': [[False, "form"], [False, "tree"]],
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'res_id': payment.id,
        }

    def _validate_payment_imputation(self):
        """ Valida los importes registrados a imputar """
        if self.advance_amount < 0 or any(line.amount < 0 for line in self.payment_imputation_line_ids):
            raise ValidationError("El importe a cuenta e importes a imputar no pueden ser menor a 0")

        if self.total <= 0:
            raise ValidationError("No se registro ningun importe a pagar")

        for imputation in self.payment_imputation_line_ids.filtered(lambda x: x.amount > 0):
            if imputation.invoice_id.residual_company_signed < imputation.amount:
                raise ValidationError("No se pueden imputar importes negativos o mayores que lo que reste pagar")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
