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
from presentation import Presentation


class PurchaseInvoicePresentation(Presentation):
    def __init__(self, with_prorate=False, builder=None, helper=None, data=None):
        self.with_prorate = with_prorate
        super(PurchaseInvoicePresentation, self).__init__(builder, helper, data)

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de compras.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ['in_invoice', 'in_refund']
                      and i.denomination_id != self.data.type_i
        )

    def create_line(self, invoice):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        line = self.builder.create_line()

        self.rate = self.helper.get_currency_rate_from_move(invoice)

        line.fecha = self.get_fecha(invoice)
        line.tipo = self.get_tipo(invoice)
        line.puntoDeVenta = self.get_puntoDeVenta(invoice)
        line.numeroComprobante = self.get_numeroComprobante(invoice)
        line.despachoImportacion = self.get_despachoImportacion(invoice)
        line.codigoDocumento = self.get_codigoDocumento(invoice)
        line.numeroVendedor = self.get_numeroPartner(invoice)
        line.denominacionVendedor = self.get_denominacionPartner(invoice)
        line.importeTotal = self.get_importeTotal(invoice)
        line.importeTotalNG = self.get_importeTotalNG(invoice)
        line.importeOpExentas = self.get_importeOpExentas(invoice)
        line.importePerOIva = self.get_importe_per_by_type(invoice, 'vat')
        line.importePerOtrosImp = self.get_importe_per_by_type(invoice, 'other')
        line.importePerIIBB = self.get_importe_per_by_type(invoice, 'gross_income')
        line.importePerIM = self.get_importe_per_by_jurisdiction(invoice, 'municipal')
        line.importeImpInt = self.get_importeImpInt(invoice)
        line.codigoMoneda = self.get_codigoMoneda(invoice)
        line.tipoCambio = self.get_tipoCambio()
        line.cantidadAlicIva = self.get_cantidadAlicIva(invoice)
        line.codigoOperacion = self.get_codigoOperacion(invoice)
        line.credFiscComp = self.get_credFiscComp(invoice)
        line.otrosTrib = self.get_otrosTrib(invoice)
        line.cuitEmisor = self.get_purchase_cuitEmisor()
        line.denominacionEmisor = self.get_purchase_denominacionEmisor()
        line.ivaComision = self.get_purchase_ivaComision()

    # ----------------CAMPOS COMPRAS----------------
    def get_puntoDeVenta(self, invoice):
        if invoice.denomination_id == self.data.type_d:
            return ''
        return super(PurchaseInvoicePresentation, self).get_puntoDeVenta()

    def get_numeroComprobante(self, invoice):
        if invoice.denomination_id == self.data.type_d:
            return ''
        return super(PurchaseInvoicePresentation, self).get_numeroComprobante()

    def get_despachoImportacion(self, invoice):
        """Si la denominacion de la factura es D, devolvemos el numero de la factura
        que es el despacho de importacion"""
        if invoice.denomination_id != self.data.type_d:
            return ''
        return invoice.name

    def get_cantidadAlicIva(self, invoice):
        """
        En caso de ser comprobante B o C se devuelve 0. En caso de que todos los impuestos sean
        exentos, se devuelve su cantidad. En caso de que haya una o mas alicuotas de iva no exentas
        se devuelve la cantidad de no exentas. En el resto de los casos se devuelve 1. A todos los
        casos se le restan la cantidad de impuestos no gravados ya que no forman parte de la cuenta.
        """
        # Si el comprobante es tipo b o c, devolvemos 0
        if invoice.denomination_id in [self.data.type_b, self.data.type_c]:
            return 0
        return super(PurchaseInvoicePresentation, self).get_cantidadAlicIva(invoice)

    def get_codigoOperacion(self, invoice):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. Actualmente no contempla el caso de importaciones
        de zona franca.
        :param invoice: record.
        :return string, ej 'N'
        """
        super(PurchaseInvoicePresentation, self).get_codigoOperacion()
        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados la operacion es no gravada.
        # En caso de que la factura tenga 0 impuestos, la condicion dara verdadero y la operacion sera no gravada.
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == self.data.tax_purchase_ng]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            return 'N'

    def get_credFiscComp(self, invoice):
        """
        Se devuelve cero en caso de que no tenga alicuotas de iva. Si tiene alicuotas y la presentacion es
        sin prorrateo, se devuelven todos los impuestos. En caso contrario se devuelve la suma de los impuestos
        de iva.
        """
        # Si la cantidad de alicuotas es igual a 0, se devuelve 0
        if self.get_cantidadAlicIva(invoice) is 0:
            return 0

        # Si es sin prorrateo , se devuelve el total de impuestos liquidado
        if not self.with_prorate:
            return self.helper.format_amount(invoice.amount_tax * self.rate)
        # Sino se devuelve el monto de los impuestos de iva
        else:
            vat_tax_amount = sum(
                invoice.tax_line_ids.filtered(
                    lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat
                ).mapped('amount'))
            return self.helper.format_amount(vat_tax_amount * self.rate)

    @staticmethod
    def get_purchase_cuitEmisor():
        return 0

    @staticmethod
    def get_purchase_denominacionEmisor():
        return ''

    @staticmethod
    def get_purchase_ivaComision():
        return 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
