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


class PurchaseInvoicePresentation:
    def __init__(self, with_prorate=False, builder=None, helper=None, data=None):
        self.with_prorate = with_prorate
        self.helper = helper
        self.builder = builder
        self.data = data

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

        line.fecha = self.get_purchase_fecha(invoice)
        line.tipo = self.get_purchase_tipo(invoice)
        line.puntoDeVenta = self.get_purchase_puntoDeVenta(invoice)
        line.numeroComprobante = self.get_purchase_numeroComprobante(invoice)
        line.despachoImportacion = self.get_purchase_despachoImportacion(invoice)
        line.codigoDocumento = self.get_purchase_codigoDocumento(invoice)
        line.numeroVendedor = self.get_purchase_numeroVendedor(invoice)
        line.denominacionVendedor = self.get_purchase_denominacionVendedor(invoice)
        line.importeTotal = self.get_purchase_importeTotal(invoice)
        line.importeTotalNG = self.get_purchase_importeTotalNG(invoice)
        line.importeOpExentas = self.get_purchase_importeOpExentas(invoice)
        line.importePerOIva = self.get_purchase_importePerOIva(invoice)
        line.importePerOtrosImp = self.get_purchase_importePerOtrosImp(invoice)
        line.importePerIIBB = self.get_purchase_importePerIIBB(invoice)
        line.importePerIM = self.get_purchase_importePerIM(invoice)
        line.importeImpInt = self.get_purchase_importeImpInt(invoice)
        line.codigoMoneda = self.get_purchase_codigoMoneda(invoice)
        line.tipoCambio = self.get_purchase_tipoCambio(invoice)
        line.cantidadAlicIva = self.get_purchase_cantidadAlicIva(invoice)
        line.codigoOperacion = self.get_purchase_codigoOperacion(invoice)
        line.credFiscComp = self.get_purchase_credFiscComp(invoice)
        line.otrosTrib = self.get_purchase_otrosTrib(invoice)
        line.cuitEmisor = self.get_purchase_cuitEmisor()
        line.denominacionEmisor = self.get_purchase_denominacionEmisor()
        line.ivaComision = self.get_purchase_ivaComision()

    # ----------------CAMPOS COMPRAS----------------
    # Campo 1
    def get_purchase_fecha(self, invoice):
        return self.helper.format_date(invoice.date_invoice)

    # Campo 2
    def get_purchase_tipo(self, invoice):
        return self.helper.get_invoice_type(invoice)

    # Campo 3
    def get_purchase_puntoDeVenta(self, invoice):
        if invoice.denomination_id == self.data.type_d:
            return ''
        return invoice.name[0:4]

    # Campo 4
    def get_purchase_numeroComprobante(self, invoice):
        if invoice.denomination_id == self.data.type_d:
            return ''
        return invoice.name[-8:]

    # Campo 5
    def get_purchase_despachoImportacion(self, invoice):
        """Si la denominacion de la factura es D, devolvemos el numero de la factura
        que es el despacho de importacion"""
        if invoice.denomination_id != self.data.type_d:
            return ''
        return invoice.name

    # Campo 6
    @staticmethod
    def get_purchase_codigoDocumento(invoice):
        """
        Obtiene el codigo de afip del tipo de documento.
        :return: char, codigo afip.
        """
        codes_model_proxy = invoice.env['codes.models.relation']

        codigoDocumento = codes_model_proxy.get_code(
            'partner.document.type',
            invoice.partner_id.partner_document_type_id.id
        )

        return codigoDocumento

    # Campo 7
    @staticmethod
    def get_purchase_numeroVendedor(invoice):
        return invoice.partner_id.vat

    # Campo 8
    @staticmethod
    def get_purchase_denominacionVendedor(invoice):
        return invoice.partner_id.name

    # Campo 9
    def get_purchase_importeTotal(self, invoice):
        """
        Devuelve el importe total de la factura
        :param invoice: record, factura.
        :param helper: instancia de PresentationTools, con herramientas de formateo.
        :return: string, monto ej: 5000->'500000' , 0->'0'
        """
        rate = self.helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_total
        return self.helper.format_amount(rate * amount)

    # Campo 10
    def get_purchase_importeTotalNG(self, invoice):
        """
        Devuelve el importe total no gravado. Si el codigo de operacion es 'N' devuelve 0.
        :param cod_ope: Codigo de operacion. ej: 'N'   
        :return: string, monto ej: 23.00-> '2300' , 0->'0'
        """
        rate = self.helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_not_taxable
        return self.helper.format_amount(rate * amount)

    # Campo 11
    def get_purchase_importeOpExentas(self, invoice):
        """
        Devuelve el monto total de importes de operaciones exentas.
        :return: string, monto ej: 23.00-> '2300' 
        """
        rate = self.helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_exempt

        return self.helper.format_amount(rate * amount)

    # Campo 12
    def get_purchase_importePerOIva(self, invoice):
        """
        Devuelve el monto total de percepciones de iva de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """

        importPerOIva = sum(
            perception.amount
            if perception.perception_id.type == 'vat'
            else 0
            for perception in invoice.perception_ids
        )

        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * importPerOIva)

    # Campo 13
    def get_purchase_importePerOtrosImp(self, invoice):
        """
        Devuelve el monto total de percepciones de otros impuestos de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """
        importePerOtrosImp = sum(
            perception.amount
            if perception.perception_id.type == 'other'
            else 0
            for perception in invoice.perception_ids
        )

        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * importePerOtrosImp)

    # Campo 14
    def get_purchase_importePerIIBB(self, invoice):
        """
        Devuelve el monto total de percepciones de ingresos brutos de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """
        importePerIIBB = sum(
            perception.amount
            if perception.perception_id.type == 'gross_income'
            else 0
            for perception in invoice.perception_ids
        )
        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * importePerIIBB)

    # Campo 15
    def get_purchase_importePerIM(self, invoice):
        """
        Devuelve el monto total de percepciones de impuestos municipales de la factura.
        :return: string, monto ej: '4500' 
        """
        importePerIM = sum(
            perception.amount
            if perception.perception_id.jurisdiction == 'municipal'
            else 0
            for perception in invoice.perception_ids
        )

        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * importePerIM)

    # Campo 16
    def get_purchase_importeImpInt(self, invoice):
        """
        Obtiene los impuestos internos de la factura formateados en string. 
        :return: string, monto ej: '2300' 
        """
        tax_group_internal = invoice.env.ref('l10n_ar.tax_group_internal')
        importeImpInt = sum(
            tax.amount
            if tax.tax_id.tax_group_id == tax_group_internal
            else 0
            for tax in invoice.tax_line_ids
        )
        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * importeImpInt)

    # Campo 17
    @staticmethod
    def get_purchase_codigoMoneda(invoice):
        """
        Obtiene el codigo de moneda de acuerdo a los mapeados en las tablas de AFIP
        Ejemplo: Las monedas Pesos y USD se mapean a PES y DOL.
        """
        codes_proxy = invoice.env["codes.models.relation"]
        model_name = "res.currency"
        model_id = invoice.currency_id.id
        return codes_proxy.get_code(model_name, model_id)

    # Campo 18
    def get_purchase_tipoCambio(self, invoice):
        "Este metodo obtiene el tipo de cambio, con las seis posiciones decimales que requiere el archivo."
        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate, 6)

    # Campo 19
    def get_purchase_cantidadAlicIva(self, invoice):
        """
        En caso de ser comprobante B o C se devuelve 0. En caso de que todos los impuestos sean
        exentos, se devuelve su cantidad. En caso de que haya una o mas alicuotas de iva no exentas
        se devuelve la cantidad de no exentas. En el resto de los casos se devuelve 1. A todos los
        casos se le restan la cantidad de impuestos no gravados ya que no forman parte de la cuenta.
        """
        # Si el comprobante es tipo b o c, devolvemos 0
        if invoice.denomination_id in [self.data.type_b, self.data.type_c]:
            return 0

        # En caso contrario devolvemos la cantidad de alicuotas de iva, o 1 si no tiene ninguna
        cantidadAlicIva = [tax for tax in invoice.tax_line_ids if tax.tax_id.tax_group_id == self.data.tax_group_vat]
        return len(cantidadAlicIva) or 1

    # Campo 20
    def get_purchase_codigoOperacion(self, invoice):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. Actualmente no contempla el caso de importaciones
        de zona franca.
        """
        # Exento:
        # Si el total de impuestos es igual al total de impuestos exentos
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if invoice.tax_line_ids and len(exempt_taxes) == len(invoice.tax_line_ids):
            return 'E'

        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados la operacion es no gravada.
        # En caso de que la factura tenga 0 impuestos, la condicion dara verdadero y la operacion sera no gravada.
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == self.data.tax_purchase_ng]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            return 'N'

        # IMPORTACIONES
        # Importaciones del exterior:
        # Si tiene despacho de importacion y este viene directo de aduana
        if invoice.denomination_id == self.data.type_d:
            return 'X'

    # Campo 21
    def get_purchase_credFiscComp(self, invoice):
        """
        Se devuelve cero en caso de que no tenga alicuotas de iva. Si tiene alicuotas y la presentacion es
        sin prorrateo, se devuelven todos los impuestos. En caso contrario se devuelve la suma de los impuestos
        de iva.
        """
        # Si la cantidad de alicuotas es igual a 0, se devuelve 0
        if self.get_purchase_cantidadAlicIva(invoice) is 0:
            return 0

        # Si es sin prorrateo , se devuelve el total de impuestos liquidado
        rate = self.helper.get_currency_rate_from_move(invoice)
        if not self.with_prorate:
            return self.helper.format_amount(invoice.amount_tax * rate)
        # Sino se devuelve el monto de los impuestos de iva
        else:
            vat_tax_amount = sum(
                invoice.tax_line_ids.filtered(
                    lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat
                ).mapped('amount'))
            return self.helper.format_amount(vat_tax_amount * rate)

    # Campo 22
    def get_purchase_otrosTrib(self, invoice):
        """
        Devuelve la suma de todos los impuestos que NO son internos, de iva, percepciones,
        en formato string
        :return: string, monto formateado. ej: '223455'
        """
        otrosTrib = 0.00
        tax_group_ids = [
            self.data.tax_group_internal,
            self.data.tax_group_vat,
            self.data.tax_group_perception
        ]
        for tax in invoice.tax_line_ids:
            otrosTrib += tax.amount if tax.tax_id.tax_group_id not in tax_group_ids else 0
        rate = self.helper.get_currency_rate_from_move(invoice)
        return self.helper.format_amount(rate * otrosTrib)

    # Campo 23
    @staticmethod
    def get_purchase_cuitEmisor():
        return 0

    # Campo 24
    @staticmethod
    def get_purchase_denominacionEmisor():
        return ''

    # Campo 25
    @staticmethod
    def get_purchase_ivaComision():
        return 0


class AccountInvoicePresentation(models.Model):
    _inherit = 'account.invoice.presentation'

    def generate_purchase_file(self):
        """
        Se genera el archivo de compras. Utiliza la API de presentaciones y tools para poder crear los archivos
        y formatear los datos.
        :return: objeto de la api (generator), con las lineas de la presentacion creadas.
        """
        # Instanciamos API, tools y datos generales
        builder = presentation_builder.Presentation('ventasCompras', 'comprasCbte')
        presentation = PurchaseInvoicePresentation(
            with_prorate=self.with_prorate,
            helper = self.helper,
            builder = builder,
            data = self.data,
        )

        return self.generate_a_file(builder, presentation)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
