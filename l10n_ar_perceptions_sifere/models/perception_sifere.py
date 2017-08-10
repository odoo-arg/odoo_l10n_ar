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
import base64
from datetime import datetime

from openerp import models, fields
from openerp.exceptions import Warning


class PerceptionSifere(models.Model):
    _name = 'perception.sifere'

    def _get_invoice_currency_rate(self, invoice):

        rate = 1

        if invoice.move_id.line_ids:
            move = invoice.move_id.line_ids[0]
            if move.amount_currency != 0:
                rate = abs((move.credit + move.debit) / move.amount_currency)

        return rate

    def generate_file(self):

        perceptions = self.env['account.invoice.perception'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('perception_id.type', '=', 'gross_income'),
            ('invoice_id.denomination_id.name', 'not in', ['D', 'X']),
            ('invoice_id.state', 'in', ['open', 'paid']),
            ('perception_id.type_tax_use', '=', 'purchase')
        ]).sorted(key=lambda r: (r.create_date, r.id))

        buffer_string = ''

        missing_vats = set()
        invalid_vats = set()
        missing_codes = set()

        for p in perceptions:

            if not p.invoice_id.partner_id.vat:
                missing_vats.add(p.invoice_id.name)

            # le puse 13 porque en V10 tenes que anexar el codigo de pais
            elif len(p.invoice_id.partner_id.vat) < 13:
                invalid_vats.add(p.invoice_id.name)

            if not p.perception_id.state_id.code:
                missing_codes.add(p.perception_id.state_id.name)

            # si ya encontro algun error, que no siga con el resto del loop porque el archivo no va a salir
            if missing_vats or invalid_vats or missing_codes:
                continue

            buffer_string += str(p.perception_id.state_id.code).zfill(3)
            buffer_string += p.invoice_id.partner_id.vat[2:4] + '-' + p.invoice_id.partner_id.vat[
                                                                      4:12] + '-' + p.invoice_id.partner_id.vat[-1:]
            buffer_string += datetime.strptime(p.create_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
            buffer_string += p.invoice_id.name[0:4]
            buffer_string += p.invoice_id.name[5:]

            currency_rate = self._get_invoice_currency_rate(p.invoice_id)

            if p.invoice_id.type == 'in_invoice':
                if p.invoice_id.is_debit_note:
                    buffer_string += 'D'
                else:
                    buffer_string += 'F'
            else:
                buffer_string += 'C'

            buffer_string += p.invoice_id.denomination_id.name

            if p.invoice_id.type == 'in_refund':
                buffer_string += '-'
            else:
                buffer_string += '0'

            buffer_string += str('{0:.2f}'.format(p.amount * currency_rate)).zfill(10).replace('.', ',')
            buffer_string += '\r\n'

        if missing_vats or invalid_vats or missing_codes:
            errors = []
            if missing_vats:
                errors.append("Los partners de las siguientes facturas no poseen numero de documento:")
                errors.extend(missing_vats)
            if invalid_vats:
                errors.append("Los partners de las siguientes facturas poseen CUIT erroneo:")
                errors.extend(invalid_vats)
            if missing_codes:
                errors.append("Las siguientes jurisdicciones no poseen codigo:")
                errors.extend(missing_codes)
            raise Warning("\n".join(errors))
        else:
            self.file = base64.encodestring(buffer_string)
            self.filename = 'per_iibb_' + str(self.date_from).replace('-', '') + '_' + str(self.date_to).replace('-',
                                                                                                                 '') + '.txt'

    name = fields.Char(string='Nombre', required=True)

    date_from = fields.Date(string='Desde', required=True)

    date_to = fields.Date(string='Hasta', required=True)

    file = fields.Binary(string='Archivo', filename="filename")

    filename = fields.Char(string='Nombre Archivo')

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        readonly=True,
        change_default=True,
        default=lambda self: self.env['res.company']._company_default_get('perception.sifere')
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
