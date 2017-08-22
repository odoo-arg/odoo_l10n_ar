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

from odoo_openpyme_api.presentations import presentation


class RetentionSifere(models.Model):
    _name = 'retention.sifere'

    def _get_importe(self, r):
        importe = str(format(r.amount))[:-2].zfill(10)
        importe_parts = [importe[:len(importe) % 3]]
        importe_parts.extend([importe[i:i + 3] for i in range(len(importe) % 3, len(importe), 3)])
        return importe_parts

    def create_line(self, code, lines, r):
        line = lines.create_line()
        line.jurisdiccion = code
        line.cuit = r.payment_id.partner_id.vat[0:2] + '-' + r.payment_id.partner_id.vat[2:10] + '-' \
                    + r.payment_id.partner_id.vat[-1:]
        line.fecha = datetime.strptime(r.create_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        line.puntoDeVenta = r.payment_id.pos_ar_id.name
        line.numeroComprobante = filter(str.isdigit, str(r.certificate_no))
        line.numeroBase = filter(str.isdigit, str("".join(r.payment_id.name.split("-"))))
        line.tipo = "R"
        line.letra = " "
        line.importe = ",".join(self._get_importe(r))

    def get_code(self, r):
        return self.env['codes.models.relation'].get_code('res.country.state', r.retention_id.state_id.id,
                                                          'ConvenioMultilateral')

    def generate_file(self):
        lines = presentation.Presentation("sifere", "retenciones")
        retentions = self.env['account.payment.retention'].search([
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to),
            ('retention_id.type', '=', 'gross_income'),
            ('payment_id.state', '=', 'posted'),
            ('payment_id.payment_type', '=', 'inbound')
        ]).sorted(key=lambda r: (r.create_date, r.id))

        missing_vats = set()
        invalid_vats = set()
        missing_codes = set()

        for r in retentions:
            code = self.get_code(r)

            if not r.payment_id.partner_id.vat:
                missing_vats.add(r.payment_id.name)
            elif len(r.payment_id.partner_id.vat) < 11:
                invalid_vats.add(r.payment_id.name)
            if not code:
                missing_codes.add(r.retention_id.state_id.name)

            self.create_line(code, lines, r)

        if missing_vats or invalid_vats or missing_codes:
            errors = []
            if missing_vats:
                errors.append("Los partners de los siguientes pagos no poseen numero de documento:")
                errors.extend(missing_vats)
            if invalid_vats:
                errors.append("Los partners de los siguientes pagos poseen CUIT erroneo:")
                errors.extend(invalid_vats)
            if missing_codes:
                errors.append("Las siguientes jurisdicciones no poseen codigo:")
                errors.extend(missing_codes)
            raise Warning("\n".join(errors))
        else:
            self.file = lines.get_encoded_string()
            self.filename = 'ret_iibb_{}_{}.txt'.format(
                str(self.date_from).replace('-', ''),
                str(self.date_to).replace('-', ''),
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
        default=lambda self: self.env['res.company']._company_default_get('retention.sifere')
    )

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
