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
from collections import defaultdict
from datetime import datetime

from openerp import models, fields, api
from openerp.exceptions import ValidationError


class WizardMoveRenumber(models.TransientModel):
    _name = 'wizard.move.renumber'

    date_from = fields.Date(
        string="Desde",
        default=fields.Date.today(),
        required=True,
    )

    date_to = fields.Date(
        string="Hasta",
        default=fields.Date.today(),
        required=True,
    )

    prefix = fields.Char(
        string="Prefijo",
    )

    minimum_digits = fields.Integer(
        string="Cantidad minima de digitos",
        required=True,
        default=1,
    )

    initial_number = fields.Integer(
        string="Numero inicial",
        required = True,
        default = 1,
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from > self.date_to:
            raise ValidationError("La fecha desde no puede ser mayor a la fecha hasta.")

    @api.constrains('initial_number')
    def check_initial_number(self):
        if self.initial_number < 1:
            raise ValidationError("El numero inicial debe ser positivo.")

    @api.constrains('minimum_digits')
    def check_minimum_digits(self):
        if self.minimum_digits < 1:
            raise ValidationError("Se debe especificar al menos un digito.")

    def renumber(self):
        moves = self.env['account.move'].search([('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        number = self.initial_number

        # Ordeno los moves por fecha y cambio los numeros
        for move in moves.sorted(lambda l: (l.date, l.id)):
            move.name = '{}{}'.format(self.prefix or '', str(number).zfill(self.minimum_digits))
            number += 1

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
