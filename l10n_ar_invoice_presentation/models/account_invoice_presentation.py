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
from openerp.exceptions import ValidationError, Warning
from datetime import datetime
from l10n_ar_api.presentations import presentation


class AccountInvoicePresentation(models.Model):
    _name = 'account.invoice.presentation'

    def get_period(self):
        """
        Genera un string con el periodo seleccionado.
        :return: string con periodo ej : '201708'
        """
        split_from = self.date_from.split('-')
        return split_from[0] + split_from[1]

    @staticmethod
    def validate_invoices(invoices):
        """
        Validamos que las facturas tengan los datos necesarios.
        :param invoices: recordset facturas
        """
        errors = []
        for partner in invoices.mapped('partner_id'):
            if not partner.property_account_position_id:
                errors.append("El partner {} no posee posicion fiscal.".format(partner.name))

            if not partner.partner_document_type_id:
                errors.append("El partner {} no posee tipo de documento.".format(partner.name))

            if not partner.vat:
                errors.append("El partner {} no posee numero de documento.".format(partner.name))

        for invoice in invoices:
            if invoice.amount_total == 0:
                errors.append("El total de la factura {} es cero.".format(invoice.name))

            if not invoice.move_id.line_ids:
                errors.append("La factura {} no posee lineas de asientos.".format(invoice.name))

        if errors:
            raise Warning(
                "ERROR\nLa presentacion no pudo ser generada por los siguientes motivos:\n{}".format("\n".join(errors))
            )

    def generate_files(self):
        """
        Genera todas las presentaciones. A cada archivo generado le pone un nombre que se usa para
        crear el nombre del fichero. Luego llama a la funcion que colocara todos los archivos en
        un fichero zip.
        """
        base_name = "REGINFO_CV_{}" + self.get_period() + ".{}"

        header_file = self.generate_header_file()
        header_file.file_name = base_name.format("CABECERA_", "txt")

        sale_file = self.generate_sale_file()
        sale_file.file_name = base_name.format("VENTAS_CBTE_", "txt")

        sale_vat_file = self.generate_sale_vat_file()
        sale_vat_file.file_name = base_name.format("VENTAS_ALICUOTAS_", "txt")

        purchase_file = self.generate_purchase_file()
        purchase_file.file_name = base_name.format("COMPRAS_CBTE_", "txt")

        purchase_vat_file = self.generate_purchase_vat_file()
        purchase_vat_file.file_name = base_name.format("COMPRAS_ALICUOTAS_", "txt")

        purchase_imports_file = self.generate_purchase_imports_file()
        purchase_imports_file.file_name = base_name.format("COMPRAS_IMPORTACION_", "txt")

        fiscal_credit_service_import_file = self.generate_fiscal_credit_service_import_file()
        fiscal_credit_service_import_file.file_name = base_name.format("CREDITO_FISCAL_SERVICIOS_", "txt")

        reginfo_zip_file = self.generate_reginfo_zip_file(
            [
                header_file,
                sale_file,
                sale_vat_file,
                purchase_file,
                purchase_vat_file,
                purchase_imports_file,
                fiscal_credit_service_import_file
            ]
        )

        self.write({
            'generation_time': datetime.now(),

            'header_filename': header_file.file_name,
            'header_file': header_file.get_encoded_string(),

            'sale_filename': sale_file.file_name,
            'sale_file': sale_file.get_encoded_string(),

            'sale_vat_filename': sale_vat_file.file_name,
            'sale_vat_file': sale_vat_file.get_encoded_string(),

            'purchase_filename': purchase_file.file_name,
            'purchase_file': purchase_file.get_encoded_string(),

            'purchase_vat_filename': purchase_vat_file.file_name,
            'purchase_vat_file': purchase_vat_file.get_encoded_string(),

            'purchase_imports_filename': purchase_imports_file.file_name,
            'purchase_imports_file': purchase_imports_file.get_encoded_string(),

            'fiscal_credit_service_import_filename': fiscal_credit_service_import_file.file_name,
            'fiscal_credit_service_import_file': fiscal_credit_service_import_file.get_encoded_string(),

            'reginfo_zip_filename': base_name.format("", "zip"),
            'reginfo_zip_file': reginfo_zip_file,
        })

    """
    Se declaran los metodos que generan las presentaciones para que puedan heredarse e implementarse
    en clases separadas. De este modo tenemos menos codigo en un solo archivo.
    """
    def generate_header_file(self):
        raise NotImplementedError

    def generate_sale_file(self):
        raise NotImplementedError

    def generate_sale_vat_file(self):
        raise NotImplementedError

    def generate_purchase_file(self):
        raise NotImplementedError

    def generate_purchase_vat_file(self):
        raise NotImplementedError

    def generate_purchase_imports_file(self):
        raise NotImplementedError

    def generate_fiscal_credit_service_import_file(self):
        raise NotImplementedError

    @staticmethod
    def generate_reginfo_zip_file(files):
        """
        Instancia el exportador en zip de ficheros de la API, y exporta todas las presentaciones.
        :param files: generators de las presentaciones
        :return: archivo zip
        """
        exporter = presentation.PresentationZipExporter()
        map(lambda file: exporter.add_element(file), files)
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
        default=lambda self: self.pool['res.company']._company_default_get(self.env.user.company_id),
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from > self.date_to:
            raise ValidationError("La fecha 'desde' no puede ser mayor a la fecha 'hasta'.")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
