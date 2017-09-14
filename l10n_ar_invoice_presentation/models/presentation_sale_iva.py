# coding: utf-8
##############################################################################
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
from openerp import models
import l10n_ar_api.presentations.presentation as presentation_builder
from presentation_tools import PresentationTools
from presentation_sale import SaleInvoicePresentation


class SaleVatInvoicePresentation:
    def __init__(self, invoice_proxy=None, date_from=None, date_to=None):
        self.invoice_proxy = invoice_proxy
        self.invoice_date_from = date_from
        self.invoice_date_to = date_to
        self.get_general_data()

    # Datos del sistema
    def get_general_data(self):
        """
        Obtiene valores predeterminados de la localizacion
        """
        self.type_b = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_b')
        self.type_c = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_c')
        self.type_d = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_d')
        self.type_i = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_i')
        self.tax_group_vat = self.invoice_proxy.env.ref('l10n_ar.tax_group_vat')

    def get_invoices(self):
        """
        Trae las facturas para generar la presentacion de ventas.
        :return: Las facturas de ventas.
        """
        invoice_proxy = self.invoice_proxy
        invoices = invoice_proxy.search(
            [
                ("type", "in", ["out_invoice", "out_refund"]),
                ("state", "not in", ["cancel", "draft"]),
                ("date_invoice", ">=", self.invoice_date_from),
                ("date_invoice", "<=", self.invoice_date_to)
            ]
        )
        return invoices

    def create_line(self, builder, invoice, helper, codes_models_proxy):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        invoice_vat_taxes = invoice.tax_line_ids.filtered(lambda t: t.tax_id.tax_group_id == self.tax_group_vat)

        tipoComprobante = SaleInvoicePresentation.get_tipo(invoice, helper)
        puntoDeVenta = SaleInvoicePresentation.get_punto_venta(invoice)
        numeroComprobante = SaleInvoicePresentation.get_numero_comprobante(invoice)

        for tax in invoice_vat_taxes:
            line = builder.create_line()
            line.tipoComprobante = tipoComprobante
            line.puntoDeVenta = puntoDeVenta
            line.numeroComprobante = numeroComprobante
            line.importeNetoGravado = self.get_importe_neto_gravado(invoice, helper)
            line.alicuotaIva = self.get_alicuota_iva(tax)
            line.impuestoLiquidado = self.get_impuesto_liquidado(invoice, tax, helper)

        # En caso que no tenga ningun impuesto, se informa una alicuota por defecto (Iva 0%)
        if not invoice_vat_taxes:
            line = builder.create_line()
            line.tipoComprobante = tipoComprobante
            line.puntoDeVenta = puntoDeVenta
            line.numeroComprobante = numeroComprobante
            line.importeNetoGravado = '0'
            line.alicuotaIva = '3'
            line.impuestoLiquidado = '0'

    @staticmethod
    def get_importe_neto_gravado(invoice, helper):
        """
        Campo 4: Importe neto gravado.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe neto gravado.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_to_tax
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_alicuota_iva(tax):
        """
        Si el impuesto es exento o no gravado, la alicuota a informar es la de 0%, y su codigo es 3,
        ya que el SIAP no contempla los codigos 1(no gravado) ni 2(exento).
        Sino se devuelve el codigo de impuesto.
        :param tax: objeto impuesto
        :param operation_code: char codigo de operacion
        """
        tax_compras_ng = tax.env.ref('l10n_ar.1_vat_no_gravado_compras')
        if tax.tax_id.is_exempt or tax.tax_id == tax_compras_ng:
            return '3'

        codes_model_proxy = tax.env['codes.models.relation']

        tax_code = codes_model_proxy.get_code(
            'account.tax',
            tax.tax_id.id
        )

        return tax_code

    @staticmethod
    def get_impuesto_liquidado(invoice, tax, helper):
        """
        Campo 6: Impuesto liquidado.
        :param invoice: La factura de la cual se sacara la informacion.
        :param tax: El impuesto de la linea de la factura.
        :param helper: Las presentation tools.
        :return: El impuesto liquidado.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = tax.amount
        return helper.format_amount(rate * amount)


class AccountInvoicePresentation(models.Model):
    _inherit = "account.invoice.presentation"

    def generate_sale_vat_file(self):
        """
        Se genera el archivo de alicuotas de ventas. Utiliza la API de presentaciones y tools para poder crear los archivos
        y formatear los datos.
        :return: objeto de la api (generator), con las lineas de la presentacion creadas.
        """
        # instanciamos el builder de la api
        builder = presentation_builder.Presentation("ventasCompras", "ventasAlicuotas")
        # instanciamos las tools de ventas-compras
        helper = PresentationTools()
        # Instanciamos helper de la presentacion puntual que estamos haciendo
        presentation = SaleVatInvoicePresentation(
            invoice_proxy=self.env["account.invoice"],
            date_from=self.date_from,
            date_to=self.date_to
        )
        # se traen todas las facturas de venta del periodo indicado
        invoices = presentation.get_invoices()
        # instanciamos los proxies
        codes_models_relation_proxy = self.env["codes.models.relation"]
        # se crea la linea de la presentacion para cada factura.
        map(
            lambda invoice: presentation.create_line(
                builder, invoice, helper, codes_models_relation_proxy
            ), invoices
        )
        return builder

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
