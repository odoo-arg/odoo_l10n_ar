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
from openerp.exceptions import UserError, ValidationError


class AccountAbstractPayment(models.AbstractModel):

    _inherit = 'account.abstract.payment'

    # Cheques recibidos
    account_third_check_ids = fields.One2many(
        'account.third.check',
        'source_payment_id',
        'Cheques de terceros'
    )
    # Cheques entregados
    account_third_check_sent_ids = fields.One2many(
        'account.third.check',
        'destination_payment_id',
        'Cheques de terceros'
    )
    account_own_check_line_ids = fields.One2many(
        'account.own.check.line',
        'payment_id',
        'Cheques propios'
    )

    @api.constrains('account_third_check_ids', 'account_own_check_line_ids', 'account_third_check_sent_ids', 'payment_type')
    def constraint_checks(self):
        """ Nos aseguramos que tenga los cheques correspondientes cada tipo de pago y su estado """

        if self.payment_type in ['outbound', 'transfer'] and self.account_third_check_ids:
            raise ValidationError("No puede haber cheques de terceros en este tipo de pago")

        elif self.payment_type in ['inbound', 'transfer'] and\
                (self.account_own_check_line_ids or self.account_third_check_sent_ids):
            raise ValidationError("No puede haber cheques propios o endosados en este tipo de pago")

    @api.onchange('account_third_check_ids', 'account_own_check_line_ids', 'account_third_check_sent_ids')
    def onchange_account_third_check_ids(self):
        self.recalculate_amount()

    def set_payment_methods_vals(self):

        vals = super(AccountAbstractPayment, self).set_payment_methods_vals()

        third_check_vals = self._get_third_check_vals()
        own_check_vals = self._get_own_check_vals()

        return vals+third_check_vals+own_check_vals

    def _get_own_check_vals(self):
        """ Obtiene los valores de montos y cuenta de los cheques de propios del pago """

        own_check_vals = []

        for line in self.account_own_check_line_ids:
            checkbook = line.own_check_id.checkbook_id
            account_id = checkbook.account_id.id or checkbook.journal_id.default_credit_account_id.id
            if not account_id:
                raise ValidationError("La cuenta bancaria no tiene cuentas contables configuradas.\n"
                                      "Por favor, configurarla en el diario correspondiente o en la chequera")

            own_check_vals.append({'amount': line.amount, 'account_id': account_id})

        return own_check_vals

    def _get_third_check_vals(self):
        """ Obtiene los valores de montos y cuenta de los cheques de terceros del pago """

        third_check_account_id = self.company_id.third_check_account_id.id
        if not third_check_account_id:
            raise UserError("No hay cuenta de cheques de terceros configurada en la empresa. \n"
                            "Por favor, configurar una.")

        # Como los cheques de terceros utilizan la misma cuenta, cargamos un solo valor en el diccionario
        amount = sum(check.amount for check in (self.account_third_check_ids | self.account_third_check_sent_ids))
        check_vals = [{'amount': amount, 'account_id': third_check_account_id}] if amount else []

        return check_vals


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    @api.multi
    def post_l10n_ar(self):
        """ Heredamos la funcion para cambiar los estados de los cheques """

        for payment in self:
            payment._validate_check_states_post()
            payment.account_third_check_ids.write({
                'state': 'wallet',
                'currency_id': payment.currency_id.id
            })
            payment.account_third_check_sent_ids.write({'state': 'handed'})
            for own_check_line in payment.account_own_check_line_ids:
                payment_date = own_check_line.issue_date if own_check_line.payment_type == 'common'\
                    else own_check_line.payment_date
                own_check_line.own_check_id.write({
                    'state': 'handed',
                    'amount': own_check_line.amount,
                    'payment_date': payment_date,
                    'issue_date': own_check_line.issue_date,
                    'destination_payment_id': payment.id,
                    'currency_id': payment.currency_id.id
                })

        return super(AccountPayment, self).post_l10n_ar()

    def cancel(self):
        """ Heredamos la funcion para cambiar los estados de los cheques """

        for payment in self:
            payment._validate_check_states_cancel()
            payment.account_third_check_ids.write({'state': 'draft'})
            payment.account_third_check_sent_ids.write({'state': 'wallet'})
            payment.account_own_check_line_ids.mapped('own_check_id').write({
                'state': 'draft',
                'destination_payment_id': None,
            })

        return super(AccountPayment, self).cancel()

    def _validate_check_states_cancel(self):
        """ Valida que los cheques esten en los estados correspondientes antes de cancelar el pago """

        if any(check.state != 'wallet' for check in self.account_third_check_ids):
            raise ValidationError("Los cheques de terceros recibidos deben estar en cartera para cancelar el pago")

        if any(check.state != 'handed' for check in self.account_third_check_sent_ids):
            raise ValidationError("Los cheques de terceros deben estar en estado entregado para cancelar el pago")

        if any(line.own_check_id.state != 'handed' for line in self.account_own_check_line_ids):
            raise ValidationError("Los cheques propios deben estar en estado entregado para cancelar el pago")

    def _validate_check_states_post(self):
        """ Valida que los cheques esten en los estados correspondientes antes de validar el pago """

        if any(check.state != 'draft' for check in self.account_third_check_ids):
            raise ValidationError("Los cheques de terceros recibidos deben estar en estado borrador")

        if any(check.state != 'wallet' for check in self.account_third_check_sent_ids):
            raise ValidationError("Los cheques de terceros entregados deben estar en cartera")

        if any(line.own_check_id.state != 'draft' for line in self.account_own_check_line_ids):
            raise ValidationError("Los cheques propios entregados deben estar en estado borrador")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
