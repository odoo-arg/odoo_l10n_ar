# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import models
import l10n_ar_api.presentations.presentation as presentation_builder
from presentation_tools import PresentationTools
from presentation_purchase import PurchaseInvoicePresentation


class PurchaseIvaPresentation:
    def __init__(self, with_prorate=False, helper=None, builder=None, data=None, purchase_presentation=None):
        self.with_prorate = with_prorate
        self.helper = helper
        self.builder = builder
        self.data = data
        self.purchase_presentation = purchase_presentation

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de alicuotas de compras.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ['in_invoice', 'in_refund']
                      and i.denomination_id not in [
                            self.data.type_b,
                            self.data.type_c,
                            self.data.type_d,
                            self.data.type_i
                        ]
        )

    def create_line(self, invoice):
        """
        Crea x lineas por cada factura, segun la cantidad de alicuotas usando el builder y el helper
        para todas las facturas que no son de importacion.
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        rate = self.helper.get_currency_rate_from_move(invoice)
        invoice_type = self.purchase_presentation.get_purchase_tipo(invoice)
        point_of_sale = self.purchase_presentation.get_purchase_puntoDeVenta(invoice)
        invoice_number = self.purchase_presentation.get_purchase_numeroComprobante(invoice)
        document_code = self.purchase_presentation.get_purchase_codigoDocumento(invoice)
        supplier_doc = self.purchase_presentation.get_purchase_numeroVendedor(invoice)
        invoice_vat_taxes = invoice.tax_line_ids.filtered(lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat)

        for tax in invoice_vat_taxes:
            line = self.builder.create_line()
            line.tipoComprobante = invoice_type
            line.puntoDeVenta = point_of_sale
            line.numeroComprobante = invoice_number
            line.codigoDocVend = document_code
            line.numeroIdVend = supplier_doc
            line.importeNetoGravado = self.get_purchase_vat_importeNetoGravado(tax, rate)
            line.alicuotaIva = self.get_purchase_vat_alicuotaIva(tax)
            line.impuestoLiquidado = self.helper.format_amount(rate * tax.amount)

        # En caso que no tenga ningun impuesto, se informa una alicuota por defecto (Iva 0%)
        if not invoice_vat_taxes:
            line = self.builder.create_line()
            line.tipoComprobante = invoice_type
            line.puntoDeVenta = point_of_sale
            line.numeroComprobante = invoice_number
            line.codigoDocVend = document_code
            line.numeroIdVend = supplier_doc
            line.importeNetoGravado = '0'
            line.alicuotaIva = '3'
            line.impuestoLiquidado = '0'

    # ----------------CAMPOS ALICUOTAS----------------
    # Campo 6
    def get_purchase_vat_importeNetoGravado(self, tax, rate):
        """
        Obtiene el neto gravado de la operacion. Para los impuestos exentos o no gravados devuelve 0.
        :param tax: objeto impuesto
        :param rate: rate de moneda. Ej: 15.63
        :param helper: tools de la presentacion
        :return: string, monto del importe
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_purchase_ng:
            return '0'
        return self.helper.format_amount(tax.base * rate)

    # Campo 7
    def get_purchase_vat_alicuotaIva(self, tax):
        """
        Si el impuesto es exento o no gravado, la alicuota a informar es la de 0%, y su codigo es 3,
        ya que el SIAP no contempla los codigos 1(no gravado) ni 2(exento).
        Sino se devuelve el codigo de impuesto.
        :param tax: objeto impuesto
        :param operation_code: char codigo de operacion
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_purchase_ng:
            return '3'

        codes_model_proxy = tax.env['codes.models.relation']

        tax_code = codes_model_proxy.get_code(
            'account.tax',
            tax.tax_id.id
        )

        return tax_code


class AccountInvoicePresentation(models.Model):

    _inherit = 'account.invoice.presentation'

    def generate_purchase_vat_file(self):
        """
        Se genera el archivo de alicuotas de compras. Utiliza la API de presentaciones y tools para poder crear los archivos
        y formatear los datos.
        :return: objeto de la api (generator), con las lineas de la presentacion creadas.
        """
        # Instanciamos API, tools y datos generales
        builder = presentation_builder.Presentation('ventasCompras', 'comprasAlicuotas')
        # Mejorar esta repeticion
        purchase_presentation = PurchaseInvoicePresentation(
            with_prorate=self.with_prorate,
            helper = self.helper,
            data = self.data,
            builder=builder,
        )
        presentation = PurchaseIvaPresentation(
            with_prorate = self.with_prorate,
            helper = self.helper,
            data = self.data,
            builder = builder,
            purchase_presentation = purchase_presentation
        )
        return self.generate_a_file(builder, presentation)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
