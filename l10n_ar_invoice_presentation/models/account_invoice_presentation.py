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

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from unidecode import unidecode

from odoo_openpyme_api.presentations import presentation


class AccountInvoicePresentation(models.Model):
    _name = 'account.invoice.presentation'

    def get_period(self):
        split_from = self.date_from.split('-')
        return split_from[0] + split_from[1]

    def generate_files(self):
        base_name = "REGINFO_CV_{}" + self.get_period() + ".{}"

        header_file = self.generate_header_file()
        header_file.file_name = base_name.format("CABECERA_", "txt")
        sale_file = self.generate_sale_file()
        sale_vat_file = self.generate_sale_vat_file()
        purchase_file = self.generate_purchase_file()
        purchase_vat_file = self.generate_purchase_vat_file()
        purchase_imports_file = self.generate_purchase_imports_file()
        fiscal_credit_service_import_file = self.generate_fiscal_credit_service_import_file()
        reginfo_zip_file = self.generate_reginfo_zip_file(
            [header_file, sale_file, sale_vat_file, purchase_file, purchase_vat_file, purchase_imports_file,
             fiscal_credit_service_import_file])

        self.write({
            'generation_time': datetime.now(),
            'header_filename': header_file.file_name,
            'header_file': header_file.get_encoded_string(),
            'sale_filename': base_name.format("VENTAS_CBTE_", "txt"),
            'sale_file': sale_file,
            'sale_vat_filename': base_name.format("VENTAS_ALICUOTAS_", "txt"),
            'sale_vat_file': sale_vat_file,
            'purchase_filename': base_name.format("COMPRAS_CBTE_", "txt"),
            'purchase_file': purchase_file,
            'purchase_vat_filename': base_name.format("COMPRAS_ALICUOTAS_", "txt"),
            'purchase_vat_file': purchase_vat_file,
            'purchase_imports_filename': base_name.format("COMPRAS_IMPORT_", "txt"),
            'purchase_imports_file': purchase_imports_file,
            'fiscal_credit_service_import_filename': base_name.format("CRED_FISCAL_IMP_SERV_", "txt"),
            'fiscal_credit_service_import_file': fiscal_credit_service_import_file,
            'reginfo_zip_filename': base_name.format("", "zip"),
            'reginfo_zip_file': reginfo_zip_file,
        })

    def generate_header_file(self):
        cabecera = presentation.Presentation("ventasCompras", "cabecera")
        line = cabecera.create_line()

        line.cuit = self.company_id.vat or 0
        line.periodo = self.get_period()
        line.secuencia = self.sequence
        line.sinMovimiento = 'S'
        if self.with_prorate:
            line.prorratearCFC = 'S'
            line.cFCGlobal = '1'
        else:
            line.prorratearCFC = 'N'
            line.cFCGlobal = '2'
        line.importeCFCG = 0
        line.importeCFCAD = 0
        line.importeCFCP = 0
        line.importeCFnCG = 0
        line.cFCSSyOC = 0
        line.cFCCSSyOC = 0

        return cabecera

    def generate_sale_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_sale_vat_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_purchase_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_purchase_vat_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_purchase_imports_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_fiscal_credit_service_import_file(self):
        return base64.encodestring(unidecode(" "))

    def generate_reginfo_zip_file(self, files):
        exporter = presentation.PresentationZipExporter()
        exporter.add_element(files[0])
        return exporter.export_elements()

    name = fields.Char(
        string="Nombre",
        required=True,
    )

    generation_time = fields.Datetime(
        string="Fecha y hora de generacion",
    )

    date_from = fields.Date(
        string="Desde",
        required=True,
    )

    date_to = fields.Date(
        string="Hasta",
        required=True,
    )

    sequence = fields.Char(
        string="Secuencia",
        size=2,
        required=True,
        default='00',
    )

    with_prorate = fields.Boolean(
        string="Con prorrateo",
    )

    header_file = fields.Binary(
        string="Cabecera",
        filename="header_filename",
    )

    header_filename = fields.Char(
        string="Nombre de archivo de cabecera",
    )

    sale_file = fields.Binary(
        string="Ventas",
        filename="sale_filename",
    )

    sale_filename = fields.Char(
        string="Nombre de archivo de ventas",
    )

    sale_vat_file = fields.Binary(
        string="Ventas alicuotas",
        filename="sale_vat_filename",
    )

    sale_vat_filename = fields.Char(
        string="Nombre de archivo de ventas alicuotas",
    )

    purchase_file = fields.Binary(
        string="Compras",
        filename="purchase_filename",
    )

    purchase_filename = fields.Char(
        string="Nombre de archivo de compras",
    )

    purchase_vat_file = fields.Binary(
        string="Compras alicuotas",
        filename="purchase_vat_filename",
    )

    purchase_vat_filename = fields.Char(
        string="Nombre de archivo de compras alicuotas",
    )

    purchase_imports_file = fields.Binary(
        string="Compras importaciones",
        filename="purchase_imports_filename",
    )

    purchase_imports_filename = fields.Char(
        string="Nombre de archivo de compras importaciones",
    )

    fiscal_credit_service_import_file = fields.Binary(
        string="Credito fiscal de importacion de servicios",
        filename="fiscal_credit_service_import_filename",
    )

    fiscal_credit_service_import_filename = fields.Char(
        string="Nombre de archivo de credito fiscal de importacion de servicios",
    )

    reginfo_zip_file = fields.Binary(
        string="ZIP de regimen de informacion",
        filename="reginfo_zip_filename",
    )

    reginfo_zip_filename = fields.Char(
        string="Nombre de archivo ZIP de regimen de informacion",
    )

    company_id = fields.Many2one(
        string="Compania",
        comodel_name="res.company",
        default=lambda self: self.pool['res.company']
            ._company_default_get(self.env.user.company_id),
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from > self.date_to:
            raise ValidationError("La fecha 'desde' no puede ser mayor a la fecha 'hasta'.")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
