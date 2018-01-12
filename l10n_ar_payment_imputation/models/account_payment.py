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

ROUND_PRECISION =  2


class AccountAbstractPayment(models.AbstractModel):

    _inherit = 'account.abstract.payment'

    @api.depends('payment_imputation_ids', 'amount', 'advance_amount')
    def _compute_payment_imputation_difference(self):
        for payment in self:
            total_imputation = sum(payment.payment_imputation_ids.mapped('amount'))
            payment.payment_imputation_difference = payment.amount - payment.advance_amount - total_imputation

    @api.onchange('payment_date')
    def onchange_payment_date(self):
        for line in self.payment_imputation_ids:
            line._get_amount_residual_in_payment_currency()

    payment_imputation_ids = fields.One2many(
        'payment.imputation.line',
        'payment_id',
        'Imputaciones',
        copy=False
    )
    payment_imputation_difference = fields.Monetary(
        compute='_compute_payment_imputation_difference',
        string='Diferencia',
        help='La resta del total del pago con las imputaciones y el importe a cuenta',
        readonly=True
    )
    advance_amount = fields.Monetary(
        'A pagar a cuenta',
        readonly=True
    )

    @api.onchange('partner_id')
    def onchange_partner_imputation(self):
        """ Elegimos las facturas pendientes de pago """
        invoice_type = 'out_invoice' if self.payment_type == 'inbound' else 'in_invoice'
        imputation_lines = []
        self.payment_imputation_ids = None
        invoice_proxy = self.env['account.invoice']
        context_invoices_ids = self.env.context.get('active_ids')

        if context_invoices_ids and self.env.context.get('active_model') == 'account.invoice':
            invoices = invoice_proxy.browse(context_invoices_ids)
        else:
            invoices = self.env['account.invoice'].search([
                ('type', '=', invoice_type),
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'open')
            ])

        for invoice in invoices:
            imputation_values = {'invoice_id': invoice.id}
            if context_invoices_ids and self.env.context.get('active_model') == 'account.invoice':
                imputation_values['amount'] = invoice.residual_company_signed
            imputation_lines.append((0, 0, imputation_values))

        self.payment_imputation_ids = imputation_lines

    def reconcile_invoices(self, move_line):
        """
        Imputa los importes del pago a las invoices en base a los importes seleccionado en las imputaciones
        :param move_line: account.move.line generada del pago
        """

        # Borramos las imputaciones que no se van a realizar
        self.payment_imputation_ids.filtered(lambda x: not x.amount).unlink()

        # Asignamos las facturas al pago
        self.invoice_ids = self.payment_imputation_ids.mapped('invoice_id')

        payment_total = abs(move_line.amount_residual) - self.advance_amount

        for imputation in self.payment_imputation_ids:

            # Tomamos las move lines de las invoices de las imputaciones
            invoice_move_line = imputation.invoice_id.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in ('payable', 'receivable')
            )
            # Calculamos los valores en multimoneda
            imputation_currency = imputation.payment_currency_id
            company_currency = imputation.payment_id.company_id.currency_id
            amount_currency = False
            currency = False
            if imputation_currency != company_currency:
                amount_currency = imputation.amount
                currency = imputation_currency

            amount = imputation_currency.with_context(date=imputation.payment_id.payment_date).\
                compute(imputation.amount, company_currency)
            payment_total -= amount

            # Validamos que no haya importes o move lines erroneas
            imputation.validate(invoice_move_line, amount)

            debit_move = move_line if move_line.debit > 0 else invoice_move_line
            credit_move = move_line if move_line.credit > 0 else invoice_move_line

            # Creamos la imputacion
            self.env['account.partial.reconcile'].create({
                'debit_move_id': debit_move.id,
                'credit_move_id': credit_move.id,
                'amount': amount,
                'amount_currency': amount_currency,
                'currency_id': currency.id if currency else currency,
            })

        # Validamos que no se haya imputado mas de lo permitido
        if round(payment_total, ROUND_PRECISION) < 0:
            raise ValidationError("El importe del pago es menor a lo que se va a imputar en los documentos, "
                                  "por favor, modificar las imputaciones para no sobrepasar el mismo.")


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    def create_imputation(self, move_line):
        """ Sobreescribimos la funcion original de imputacion para que realice por las invoices seleccionadas """
        if self.payment_imputation_ids:
            self.reconcile_invoices(move_line)
        else:
            super(AccountPayment, self).create_imputation(move_line)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
