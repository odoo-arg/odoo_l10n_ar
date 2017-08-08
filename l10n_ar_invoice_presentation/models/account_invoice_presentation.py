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

from openerp import models, fields, api
from openerp.exceptions import ValidationError
from unidecode import unidecode


class AccountInvoicePresentation(models.Model):
    _name = 'account.invoice.presentation'

    def generate_files(self):
        header_file = self.generate_header_file()
        sale_file = self.generate_sale_file()
        sale_vat_file = self.generate_sale_vat_file()
        purchase_file = self.generate_purchase_file()
        purchase_vat_file = self.generate_purchase_vat_file()
        purchase_imports_file = self.generate_purchase_imports_file()
        fiscal_credit_service_import_file = self.generate_fiscal_credit_service_import_file()
        reginfo_zip_file = self.generate_reginfo_zip_file()

        self.write({
            'header_filename': 'A.txt',
            'header_file': header_file,
            'sale_filename': 'B.txt',
            'sale_file': sale_file,
            'sale_vat_filename': 'C.txt',
            'sale_vat_file': sale_vat_file,
            'purchase_filename': 'D.txt',
            'purchase_file': purchase_file,
            'purchase_vat_filename': 'E.txt',
            'purchase_vat_file': purchase_vat_file,
            'purchase_imports_filename': 'F.txt',
            'purchase_imports_file': purchase_imports_file,
            'fiscal_credit_service_import_filename': 'G.txt',
            'fiscal_credit_service_import_file': fiscal_credit_service_import_file,
            'reginfo_zip_filename': 'H.txt',
            'reginfo_zip_file': reginfo_zip_file,
        })

    def generate_header_file(self):
        return base64.encodestring(unidecode(" "))

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

    def generate_reginfo_zip_file(self):
        return base64.encodestring(unidecode(" "))

    name = fields.Char(
        string="Nombre",
        required=True,
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
