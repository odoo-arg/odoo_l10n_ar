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
from datetime import datetime

from openerp import models, fields
from openerp.exceptions import Warning

from odoo_openpyme_api.presentations import presentation


class PerceptionSifere(models.Model):
    _name = 'perception.sifere'

    def _get_invoice_currency_rate(self, invoice):
        rate = 1
        if invoice.move_id.line_ids:
            move = invoice.move_id.line_ids[0]
            if move.amount_currency != 0:
                rate = abs((move.credit + move.debit) / move.amount_currency)
        return rate

    def _get_tipo(self, p):
        if p.invoice_id.type == 'in_invoice':
            return 'D' if p.invoice_id.is_debit_note else 'F'
        else:
            return 'C'

    def _get_invalid_denomination(self):
        return self.env.ref('l10n_ar_afip_tables.account_denomination_d').name

    def _get_importe(self, p):
        importe = str(format(p.amount * self._get_invoice_currency_rate(p.invoice_id)))[:-2].zfill(10)
        importe_parts = [importe[:len(importe) % 3]]
        importe_parts.extend([importe[i:i + 3] for i in range(len(importe) % 3, len(importe), 3)])
        return importe_parts

    def get_code(self, p):
        return self.env['codes.models.relation'].get_code('res.country.state', p.perception_id.state_id.id,
                                                          'ConvenioMultilateral')

    def create_line(self, code, lines, p):
        line = lines.create_line()
        line.jurisdiccion = code
        line.cuit = p.invoice_id.partner_id.vat[0:2] + '-' + p.invoice_id.partner_id.vat[2:10] + '-' \
                    + p.invoice_id.partner_id.vat[-1:]
        line.fecha = datetime.strptime(p.create_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        line.puntoDeVenta = p.invoice_id.name[0:4]
        line.numeroComprobante = p.invoice_id.name[5:]
        line.tipo = self._get_tipo(p)
        line.letra = p.invoice_id.denomination_id.name
        line.importe = ",".join(self._get_importe(p))

    def generate_file(self):
        lines = presentation.Presentation("sifere", "percepciones")
        perceptions = self.env['account.invoice.perception'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('perception_id.type', '=', 'gross_income'),
            ('invoice_id.denomination_id.name', '!=', self._get_invalid_denomination()),
            ('invoice_id.state', 'in', ['open', 'paid']),
            ('perception_id.type_tax_use', '=', 'purchase')
        ]).sorted(key=lambda r: (r.create_date, r.id))

        missing_vats = set()
        invalid_vats = set()
        missing_codes = set()

        for p in perceptions:
            code = self.get_code(p)

            if not p.invoice_id.partner_id.vat or p.invoice_id.partner_id.partner_document_type_id != self.env.ref('l10n_ar_afip_tables.partner_document_type_80'):
                missing_vats.add(p.invoice_id.name)
            elif len(p.invoice_id.partner_id.vat) < 11:
                invalid_vats.add(p.invoice_id.name)
            if not code:
                missing_codes.add(p.perception_id.state_id.name)

            # si ya encontro algun error, que no siga con el resto del loop porque el archivo no va a salir
            if missing_vats or invalid_vats or missing_codes:
                continue
            self.create_line(code, lines, p)

        if missing_vats or invalid_vats or missing_codes:
            errors = []
            if missing_vats:
                errors.append("Los partners de las siguientes facturas no poseen CUIT:")
                errors.extend(missing_vats)
            if invalid_vats:
                errors.append("Los partners de las siguientes facturas poseen CUIT erroneo:")
                errors.extend(invalid_vats)
            if missing_codes:
                errors.append("Las siguientes jurisdicciones no poseen codigo:")
                errors.extend(missing_codes)
            raise Warning("\n".join(errors))
        else:
            self.file = lines.get_encoded_string()
            self.filename = 'per_iibb_{}_{}.txt'.format(
                str(self.date_from).replace('-', ''),
                str(self.date_to).replace('-', '')
            )

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
