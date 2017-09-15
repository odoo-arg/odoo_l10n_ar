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
from presentation_purchase import PurchaseInvoicePresentation


class PurchaseIvaPresentation(PurchaseInvoicePresentation):
    def __init__(self, builder, data):
        super(PurchaseIvaPresentation, self).__init__(builder, data)

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
        :param invoice: record, factura
        """
        self.rate = self.helper.get_currency_rate_from_move(invoice)

        invoice_type = self.get_tipo(invoice)
        point_of_sale = self.get_puntoDeVenta(invoice)
        invoice_number = self.get_numeroComprobante(invoice)
        document_code = self.get_codigoDocumento(invoice)
        supplier_doc = self.get_numeroPartner(invoice)

        invoice_vat_taxes = invoice.tax_line_ids.filtered(lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat)

        for tax in invoice_vat_taxes:
            line = self.builder.create_line()
            line.tipoComprobante = invoice_type
            line.puntoDeVenta = point_of_sale
            line.numeroComprobante = invoice_number
            line.codigoDocVend = document_code
            line.numeroIdVend = supplier_doc
            line.importeNetoGravado = self.get_importeNetoGravado(tax)
            line.alicuotaIva = self.get_alicuotaIva(tax)
            line.impuestoLiquidado = self.get_impuestoLiquidado(tax)

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

    def get_importeNetoGravado(self, tax):
        """
        Obtiene el neto gravado de la operacion. Para los impuestos exentos o no gravados devuelve 0.
        :param tax: objeto impuesto
        :return: string, monto del importe
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_purchase_ng:
            return '0'
        return self.helper.format_amount(tax.base * self.rate)

    def get_alicuotaIva(self, tax):
        """
        Si el impuesto es exento o no gravado, la alicuota a informar es la de 0%, y su codigo es 3,
        ya que el SIAP no contempla los codigos 1(no gravado) ni 2(exento).
        :param tax: objeto impuesto
        :return integer, codigo de impuesto afip, ej: 5 
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_purchase_ng:
            return '3'

        return super(PurchaseIvaPresentation, self).get_alicuotaIva(tax)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
