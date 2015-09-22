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
from openerp.exceptions import Warning


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    perception_ids = fields.One2many(
        'perception.tax.line',
        'invoice_id',
        string='Percepcion',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    #~ SE COMENTA PARTE DE ESTA FUNCION PARA NO ESCRIBIR LA MOVE LINE CON EL IMPORTE BASE DE LA PERCEPCION
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):

        '''
        # Como nos faltan los account.move.line de las bases imponibles de las percepciones
        # utilizamos este hook para agregarlos

        company_currency = self.company_id.currency_id.id
        current_currency = self.currency_id.id
        '''

        for p in self.perception_ids:

            #~ ESCRIBIMOS LA FECHA DE LA FACTURA EN LA PERCEPCIONES PARA AQUELLAS
            #~ QUE NO TENIAN UNA FECHA.
            if not p.date:

                p.date = self.date_invoice or time.strftime('%Y-%m-%d')

            '''
            sign = p.perception_id.tax_id.base_sign

            tax_amount, base_amount = p._compute(self, p.base, p.amount)

            # ...y ahora creamos la linea contable perteneciente a la base imponible de la perception
            # Notar que credit & debit son 0.0 ambas. Lo que cuenta es el tax_code_id y el tax_amount
            move_line = {
                'name': p.name + '(Base Imp)',
                'ref': self.internal_number or False,
                'debit': 0.0,
                'credit': 0.0,
                'account_id': p.account_id.id,
                'tax_code_id': p.base_code_id.id,
                'tax_amount': base_amount,
                'journal_id': self.journal_id.id,
                'period_id': self.period_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': company_currency != current_currency and sign * p.amount or 0.0,
                'date': self.date_invoice or time.strftime('%Y-%m-%d'),
                'date_maturity': self.date_due or False,
            }

            move_lines.insert(len(move_lines) - 1, (0, 0, move_line))
            '''
        return move_lines

AccountInvoice()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
