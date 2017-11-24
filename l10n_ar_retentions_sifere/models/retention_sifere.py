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

from l10n_ar_api.presentations import presentation
from openerp import models, fields
from openerp.exceptions import Warning


class RetentionSifere(models.Model):
    _name = 'retention.sifere'

    def get_code(self, r):
        return self.env['codes.models.relation'].get_code('res.country.state', r.retention_id.state_id.id,
                                                          'ConvenioMultilateral')

    def partner_document_type_not_cuit(self, partner):
        return partner.partner_document_type_id != self.env.ref('l10n_ar_afip_tables.partner_document_type_80')

    def create_line(self, code, lines, r):
        line = lines.create_line()
        line.jurisdiccion = code
        vat = r.payment_id.partner_id.vat
        line.cuit = "{0}-{1}-{2}".format(vat[0:2], vat[2:10], vat[-1:])
        line.fecha = datetime.strptime(r.create_date, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y')
        line.puntoDeVenta = r.payment_id.pos_ar_id.name
        line.numeroComprobante = filter(str.isdigit, str(r.certificate_no))
        line.numeroBase = filter(str.isdigit, str(r.payment_id.name.split('-')[1]))
        line.tipo = "R"
        line.letra = " "
        line.importe = '{0:.2f}'.format(r.amount).replace('.', ',')

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
        invalid_doctypes = set()
        invalid_vats = set()
        missing_codes = set()

        for r in retentions:
            code = self.get_code(r)

            vat = r.payment_id.partner_id.vat
            if not vat:
                missing_vats.add(r.payment_id.name_get()[0][1])
            elif len(vat) < 11:
                invalid_vats.add(r.payment_id.name_get()[0][1])
            if self.partner_document_type_not_cuit(r.payment_id.partner_id):
                invalid_doctypes.add(r.payment_id.name_get()[0][1])
            if not code:
                missing_codes.add(r.retention_id.state_id.name)

            # si ya encontro algun error, que no siga con el resto del loop porque el archivo no va a salir
            # pero que siga revisando las retenciones por si hay mas errores, para mostrarlos todos juntos
            if missing_vats or invalid_doctypes or invalid_vats or missing_codes:
                continue
            self.create_line(code, lines, r)

        if missing_vats or invalid_doctypes or invalid_vats or missing_codes:
            errors = []
            if missing_vats:
                errors.append("Los partners de los siguientes pagos no poseen numero de CUIT:")
                errors.extend(missing_vats)
            if invalid_doctypes:
                errors.append("El tipo de documento de los partners de los siguientes pagos no es CUIT:")
                errors.extend(invalid_doctypes)
            if invalid_vats:
                errors.append("Los partners de los siguientes pagos poseen numero de CUIT erroneo:")
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
