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
    def __init__(self):
        self.invoice_proxy = None
        self.invoice_date_from = None
        self.invoice_date_to = None

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
        tax_group_vat = invoice.env.ref("l10n_ar.tax_group_vat")
        if SaleInvoicePresentation.get_cantidad_alic_iva(invoice) > 0:
            for tax in invoice.tax_line_ids:
                if (
                    tax.tax_id.tax_group_id != tax_group_vat
                    and SaleInvoicePresentation.get_codigo_operacion(invoice) != 'N'
                ):
                    continue
                line = builder.create_line()
                # campo 1: tipo de comprobante
                line.tipoComprobante = SaleInvoicePresentation.get_tipo(invoice, helper)
                # campo 2: punto de venta
                line.puntoDeVenta = SaleInvoicePresentation.get_punto_venta(invoice)
                # campo 3: numero de comprobante
                line.numeroComprobante = SaleInvoicePresentation.get_numero_comprobante(invoice)
                # campo 4: importe neto gravado
                line.importeNetoGravado = self.get_importe_neto_gravado(invoice, helper)
                # campo 5: alicuota de iva
                line.alicuotaIva = self.get_alicuota_iva(invoice, tax, codes_models_proxy, helper)
                # campo 6: impuesto liquidado
                line.impuestoLiquidado = self.get_impuesto_liquidado(invoice, tax, helper)

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
    def get_alicuota_iva(invoice, tax, codes_models_proxy, helper):
        """
        Campo 5: Alicuota de IVA.
        :param invoice: La factura de la cual se sacara la informacion.
        :param tax: El impuesto de la linea de la factura (o uno de ellos).
        :param codes_models_proxy: El proxy de codes models relation.
        :return: La alicuota de IVA.
        """
        if SaleInvoicePresentation.get_codigo_operacion(invoice) in ["E","N"]:
            return "3"
        tax_code = codes_models_proxy.get_code("account.tax", tax.tax_id.id)
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
        presentation = SaleVatInvoicePresentation()
        # escribimos las propiedades de SaleVatInvoicePresentation
        presentation.invoice_proxy = self.env["account.invoice"]
        presentation.invoice_date_from = self.date_from
        presentation.invoice_date_to = self.date_to
        # se traen todas las facturas de venta del periodo indicado
        invoices = presentation.get_invoices()
        # validamos tener todos los datos necesarios
        self.validate_invoices(invoices)
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
