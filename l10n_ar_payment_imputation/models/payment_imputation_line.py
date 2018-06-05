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


class AccountPaymentImputationLine(models.Model):

    _name = 'payment.imputation.line'

    @api.depends('payment_currency_id', 'invoice_amount_residual_company')
    def _get_amount_residual_in_payment_currency(self):
        for line in self:
            company_currency = line.env.user.company_id.currency_id
            payment_currency = line.payment_id.currency_id
            if company_currency != payment_currency:
                amount = company_currency.with_context(date=line.payment_id.payment_date).\
                    compute(line.invoice_amount_residual_company, payment_currency)
            else:
                amount = line.invoice_amount_residual_company

            line.amount_residual_in_payment_currency = amount

    invoice_id = fields.Many2one('account.invoice', 'Documento', required=True)
    payment_id = fields.Many2one('account.payment', 'Pago', ondelete='cascade')
    payment_currency_id = fields.Many2one(related='payment_id.currency_id')
    amount = fields.Monetary('Total A imputar', currency_field='payment_currency_id')
    payment_state = fields.Selection(related='payment_id.state')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    company_currency_id = fields.Many2one(related='invoice_id.company_currency_id')
    invoice_amount_residual = fields.Monetary(related='invoice_id.residual_signed')
    invoice_amount_total = fields.Monetary(related='invoice_id.amount_total_signed')
    invoice_amount_residual_company = fields.Monetary(related='invoice_id.residual_company_signed')
    invoice_amount_company = fields.Monetary(related='invoice_id.amount_total_company_signed')
    company_id = fields.Many2one('res.company', string='Compania', related='payment_id.company_id', store=True,
                                 readonly=True, related_sudo=False)
    amount_residual_in_payment_currency = fields.Monetary(
        'Restante moneda pago',
        'payment_currency_id',
        compute=_get_amount_residual_in_payment_currency
    )

    def validate(self, invoice_move_line, amount):
        """
        Valida que no haya problemas a la necesitar generar una imputacion a una invoice
        :param invoice_move_line: account.move.line de la invoice
        :param amount: Importe que se va a imputar
        """

        self.ensure_one()

        # Caso que se modifique el asiento y deje inconsistencia
        if len(invoice_move_line) != 1:
            raise ValidationError("El asiento de la factura que se quiere imputar no tiene cuentas deudoras "
                                  "o tiene mas de una asociada, por favor, modificar el asiento primero")

        if self.invoice_amount_residual_company < amount or amount < 0:
            raise ValidationError("No se pueden imputar importes negativos o mayores que lo que reste pagar")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
