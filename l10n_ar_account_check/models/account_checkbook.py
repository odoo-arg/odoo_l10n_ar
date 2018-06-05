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


class AccountCheckbook(models.Model):

    _name = 'account.checkbook'
    _inherit = ['mail.thread']

    @api.depends('account_own_check_ids')
    def _get_checks(self):
        for checkbook in self:
            checkbook.account_draft_own_check_ids = \
                checkbook.account_own_check_ids.filtered(lambda x: x.state == 'draft')
            checkbook.account_used_own_check_ids = \
                checkbook.account_own_check_ids.filtered(lambda x: x.state != 'draft')

    @api.multi
    def _search_draft_checks(self, operator, value):
        recs = self.env['account.own.check'].search([('state', '=', 'draft')])
        return [('id', 'in', recs.ids)]

    name = fields.Char('Referencia', required=True, track_visibility='onchange')
    account_id = fields.Many2one(
        'account.account',
        'Cuenta',
        help="Seleccionar una cuenta contable si no se desea utilizar la de la cuenta bancaria",
        track_visibility='onchange'
    )
    payment_type = fields.Selection(
        [('common', 'Comun'),
         ('postdated', 'Diferido')],
        string="Tipo",
        required=True,
        default='common',
        track_visibility='onchange'
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Cuenta bancaria',
        domain=[('type', '=', 'bank')],
        required=True,
        track_visibility='onchange'
    )
    account_own_check_ids = fields.One2many(
        'account.own.check',
        'checkbook_id',
        'Cheques'
    )
    account_draft_own_check_ids = fields.One2many(
        'account.own.check',
        'checkbook_id',
        'Cheques',
        compute=_get_checks,
        search=_search_draft_checks
    )
    account_used_own_check_ids = fields.One2many(
        'account.own.check',
        'checkbook_id',
        'Cheques',
        compute=_get_checks

    )
    number_from = fields.Char('Desde', required=True, track_visibility='onchange')
    number_to = fields.Char('Hasta', required=True, track_visibility='onchange')

    active = fields.Boolean(string='Activo', default=True, track_visibility='onchange')

    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='journal_id.currency_id',
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Compania',
        required=True,
        default=lambda self: self.env.user.company_id,
    )

    @api.constrains('number_from', 'number_to')
    def constraint_numbers(self, max_checks=100):
        for checkbook in self:

            if not (checkbook.number_from.isdigit() or checkbook.number_to.isdigit()):
                raise ValidationError("La numeracion debe contener solo numeros")

            if int(checkbook.number_from) <= 0 or int(checkbook.number_to) <= 0:
                raise ValidationError("La numeracion debe ser mayor a cero.")

            if int(checkbook.number_from) > int(checkbook.number_to):
                raise ValidationError("Numeracion Desde no puede ser mayor a Hasta.")

            if int(checkbook.number_to) - int(checkbook.number_from) + 1 > max_checks:
                raise ValidationError("El rango de cheques de la chequera es muy grande.\n"
                                      "No puede superar los {} cheques".format(max_checks))

    def generate_checks(self):
        """ Crea todos los cheques faltantes de cada chequera seleccionada """

        for checkbook in self:

            if self.account_used_own_check_ids:
                raise ValidationError("Solo se pueden generar cheques en una chequera no utilizada.")

            total_numbers = range(int(checkbook.number_from), int(checkbook.number_to)+1)

            checkbook._validate_checkbook_fields()
            bank_id = checkbook.journal_id.bank_id.id

            # Borramos los cheques viejos en caso que ninguno se haya usado, por si cambian el rango
            if not checkbook.account_used_own_check_ids:
                checkbook.account_own_check_ids.unlink()

            # El nombre del cheque puede contener solo digitos
            actual_numbers = [int(number) for number in checkbook.account_own_check_ids.mapped('name')]

            # Creamos cheques segun la numeracion de la chequera para los cheques no existentes
            for check_number in set(total_numbers) - set(actual_numbers):
                self.account_own_check_ids.create({
                    'checkbook_id': checkbook.id,
                    'name': str(check_number),
                    'bank_id': bank_id,
                    'payment_type': checkbook.payment_type,
                    'currency_id': checkbook.currency_id.id or self.env.user.company_id.currency_id.id,
                })

    def _validate_checkbook_fields(self):
        if not self.journal_id.bank_id:
            raise ValidationError("Falta configurar el banco en la cuenta bancaria de la chequera")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
