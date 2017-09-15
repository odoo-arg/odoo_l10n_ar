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


class SaleInvoicePresentation:
    def __init__(self, builder, helper, data):
        self.builder = builder
        self.helper = helper
        self.data = data

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de alicuotas de compras.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ["out_invoice", "out_refund"]
        )

    def generate(self, invoices):
        filtered_invoices = self.filter_invoices(invoices)
        map(lambda invoice: self.create_line(invoice), filtered_invoices)
        return self.builder

    def create_line(self, invoice):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        line = self.builder.create_line()

        self.rate = self.helper.get_currency_rate_from_move(invoice)

        # campo 1: fecha de comprobante
        line.fecha = self.get_fecha(invoice)
        # campo 2: tipo de comprobante
        line.tipo = self.get_tipo(invoice)
        # campo 3: punto de Venta
        line.puntoDeVenta = self.get_punto_venta(invoice)
        # campo 4: numero de comprobante
        line.numeroComprobante = self.get_numero_comprobante(invoice)
        # campo 5: numero de comprobante hasta
        line.numeroHasta = self.get_numero_comprobante(invoice)
        # campo 6: codigo de documento del comprador
        line.codigoDocumento = self.get_codigo_documento(invoice)
        # campo 7: numero de identificacion del comprador
        line.numeroComprador = self.get_numero_comprador(invoice)
        # campo 8: apellido y nombre del comprador
        line.denominacionComprador = self.get_denominacion_comprador(invoice)
        # campo 9: importe total de la operacion
        line.importeTotal = self.get_importe_total(invoice)
        # campo 10: importe total de conceptos que no integran el precio neto gravado
        line.importeTotalNG = self.get_importe_total_ng(invoice)
        # Campos 11, 13, 14 y 15 (Percepciones)
        self.fill_perceptions(invoice, line)
        # campo 12: importe de operaciones exentas
        line.importeExentos = self.get_importe_exentos(invoice)
        # campo 16: importe de impuestos internos
        line.importeImpInt = self.get_importe_imp_int(invoice)
        # campo 17: codigo de moneda
        line.codigoMoneda = self.get_codigo_moneda(invoice)
        # campo 18: tipo de cambio
        line.tipoCambio = self.get_tipo_cambio(invoice)
        # campo 19: cantidad de alicuotas de IVA
        line.cantidadAlicIva = self.get_cantidad_alic_iva(invoice)
        # campo 20: codigo de operacion
        line.codigoOperacion = self.get_codigo_operacion(invoice)
        # campo 21: otros tributos
        line.otrosTributos = self.get_otros_tributos(invoice)
        # campo 22: fecha de vencimiento de pago
        line.fechaVtoPago = self.get_fecha_vto_pago(invoice)

    def fill_perceptions(self, invoice, line):
        if invoice.partner_id.property_account_position_id == self.data.tax_purchase_ng:
            line.percepcionNC = self.get_percepcion_nc(invoice)
        else:
            line.importePercepciones = self.get_importe_per_by_jurisdiction(invoice, 'nacional')
            line.importePerIM = self.get_importe_per_by_jurisdiction(invoice, 'municipal')
            line.importePerIIBB = self.get_importe_per_by_type(invoice, 'gross_income')

    def get_percepcion_nc(self, invoice):
        """
        Campo 11: Percepcion a no categorizados.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La percepcion a no categorizados.
        """
        amount = sum(invoice.perception_ids.mapped("amount")) \
            if invoice.partner_id.property_account_position_id == self.data.tax_purchase_ng \
            else 0
        return self.helper.format_amount(self.rate * amount)

    def get_fecha_vto_pago(self, invoice):
        """
        Campo 22: Fecha de vencimiento de pago. Sólo se informará cuando la prestación se corresponda 
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
