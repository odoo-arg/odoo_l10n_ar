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
from presentation_sale import SaleInvoicePresentation


class SaleVatInvoicePresentation(SaleInvoicePresentation):
    def __init__(self, builder, data):
        super(SaleVatInvoicePresentation, self).__init__(builder, data)

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de alicuotas de ventas.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ["out_invoice", "out_refund"]
        )

    def create_line(self, invoice):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param invoice: record, factura
        """
        self.rate = self.helper.get_currency_rate_from_move(invoice)

        tipoComprobante = self.get_tipo(invoice)
        puntoDeVenta = self.get_puntoDeVenta(invoice)
        numeroComprobante = self.get_numeroComprobante(invoice)

        invoice_vat_taxes = invoice.tax_line_ids.filtered(lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat)

        for tax in invoice_vat_taxes:
            line = self.builder.create_line()

            line.tipoComprobante = tipoComprobante
            line.puntoDeVenta = puntoDeVenta
            line.numeroComprobante = numeroComprobante
            line.importeNetoGravado = self.get_importeNetoGravado(invoice)
            line.alicuotaIva = self.get_alicuotaIva(tax)
            line.impuestoLiquidado = self.get_impuestoLiquidado(invoice, tax)

        # En caso que no tenga ningun impuesto, se informa una alicuota por defecto (Iva 0%)
        if not invoice_vat_taxes:
            line = self.builder.create_line()
            line.tipoComprobante = tipoComprobante
            line.puntoDeVenta = puntoDeVenta
            line.numeroComprobante = numeroComprobante
            line.importeNetoGravado = '0'
            line.alicuotaIva = '3'
            line.impuestoLiquidado = '0'

    def get_importeNetoGravado(self, tax):
        """
        Obtiene el neto gravado de la operacion. Para los impuestos exentos o no gravados devuelve 0.
        :param tax: objeto impuesto
        :return: string, monto del importe
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_sale_ng:
            return '0'
        return self.helper.format_amount(tax.base * self.rate)

    def get_alicuotaIva(self, tax):
        """
        Si el impuesto es exento o no gravado, la alicuota a informar es la de 0%, y su codigo es 3,
        ya que el SIAP no contempla los codigos 1(no gravado) ni 2(exento).
        :param tax: objeto impuesto
        :param operation_code: char codigo de operacion
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_sale_ng:
            return '3'

        return super(SaleVatInvoicePresentation, self).get_alicuotaIva(tax)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
