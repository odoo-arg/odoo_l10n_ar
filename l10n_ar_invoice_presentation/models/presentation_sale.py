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
from presentation import Presentation


class SaleInvoicePresentation(Presentation):
    def __init__(self, builder, data):
        super(SaleInvoicePresentation, self).__init__(builder, data)

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de ventas.
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
        line = self.builder.create_line()

        self.rate = self.helper.get_currency_rate_from_move(invoice)

        line.fecha = self.get_fecha(invoice)
        line.tipo = self.get_tipo(invoice)
        line.puntoDeVenta = self.get_puntoDeVenta(invoice)
        line.numeroComprobante = self.get_numeroComprobante(invoice)
        line.numeroHasta = self.get_numeroComprobante(invoice)
        line.codigoDocumento = self.get_codigoDocumento(invoice)
        line.numeroComprador = self.get_numeroPartner(invoice)
        line.denominacionComprador = self.get_denominacionPartner(invoice)
        line.importeTotal = self.get_importeTotal(invoice)
        line.importeTotalNG = self.get_importeTotalNG(invoice)
        self.fill_perceptions(invoice, line)
        line.importeExentos = self.get_importeOpExentas(invoice)
        line.importeImpInt = self.get_importeImpInt(invoice)
        line.codigoMoneda = self.get_codigoMoneda(invoice)
        line.tipoCambio = self.get_tipoCambio(invoice)
        line.cantidadAlicIva = self.get_cantidadAlicIva(invoice)
        line.codigoOperacion = self.get_codigoOperacion(invoice)
        line.otrosTributos = self.get_otrosTrib(invoice)
        line.fechaVtoPago = self.get_fecha_vto_pago()

    def fill_perceptions(self, invoice, line):
        if invoice.partner_id.property_account_position_id == self.data.tax_sale_ng:
            line.percepcionNC = self.get_percepcion_nc(invoice)
        else:
            line.importePercepciones = self.get_importe_per_by_jurisdiction(invoice, 'nacional')
            line.importePerIM = self.get_importe_per_by_jurisdiction(invoice, 'municipal')
            line.importePerIIBB = self.get_importe_per_by_type(invoice, 'gross_income')

    def get_percepcion_nc(self, invoice):
        """
        Percepcion a no categorizados. 
        :param invoice: record.
        :return: string, importe percepcion nc, ej: '2134'
        """
        amount = sum(invoice.perception_ids.mapped("amount")) \
            if invoice.partner_id.property_account_position_id == self.data.tax_sale_ng \
            else 0
        return self.helper.format_amount(self.rate * amount)

    def get_codigoOperacion(self, invoice):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. Actualmente no contempla el caso de importaciones
        de zona franca.
        :param invoice: record.
        :return string, ej 'N'
        """
        super(SaleInvoicePresentation, self).get_codigoOperacion()
        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados la operacion es no gravada.
        # En caso de que la factura tenga 0 impuestos, la condicion dara verdadero y la operacion sera no gravada.
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == self.data.tax_sale_ng]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            return 'N'

    @staticmethod
    def get_fecha_vto_pago():
        """
        Fecha de vencimiento de pago. Sólo se informará cuando la prestación se corresponda 
        con un servicio público, siendo obligatorio para los comprobantes tipo '017 - Liquidación de 
        Servicios Públicos Clase A' y '018 – Liquidación de Servicios Públicos Clase B' y opcional 
        para el resto de los comprobantes.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La fecha de vencimiento de pago.
        """
        # TODO: no implementado
        return "".zfill(8)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
