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
import abc
from presentation_tools import PresentationTools


class Presentation:
    __metaclass__ = abc.ABCMeta

    def __init__(self, builder, data):
        self.helper = PresentationTools()
        self.data = data
        self.builder = builder
        self.rate = None

    def filter_invoices(self, invoices):
        raise NotImplementedError

    def create_line(self, invoice):
        raise NotImplementedError

    def generate(self, invoices):
        """
        Genera la presentacion usando las facturas filtradas por el tipo de presentacion
        especifico.
        :param invoices: recordset, todas las facturas.
        :return: objeto de la api.
        """
        filtered_invoices = self.filter_invoices(invoices)
        map(lambda invoice: self.create_line(invoice), filtered_invoices)
        return self.builder

    def get_fecha(self, invoice):
        return self.helper.format_date(invoice.date_invoice)

    def get_tipo(self, invoice):
        return self.helper.get_invoice_type(invoice)

    def get_puntoDeVenta(self, invoice):
        """
        Punto de venta. Se obtiene de los primeros 4 digitos del numero del comprobante.
        :param invoice: record.
        :return: string, ej: '0001'.
        """
        return invoice.name[0:4]

    def get_numeroComprobante(self, invoice):
        """
        Numero de comprobante. Se obtiene a partir de los ultimos 8 digitos del numero
        del comprobante.
        :param invoice: record.
        :return: string, ej: '00000001'.
        """
        return invoice.name[-8:]

    def get_codigoDocumento(self, invoice):
        """
        Codigo de documento del partner. Se obtiene a partir de la tabla de afip,
        comparando con el id del tipo de documento del partner de la factura.
        :param invoice: record.
        :return: string, ej: '80'
        """
        codigo_documento = self.data.codes_model_proxy.get_code(
            "partner.document.type",
            invoice.partner_id.partner_document_type_id.id
        )
        return codigo_documento

    def get_numeroPartner(self, invoice):
        """
        Numero de identificacion del partner. Se obtiene del campo vat del partner de la factura.
        :param invoice: record.
        :return: string, ej: '20359891033'
        """
        return invoice.partner_id.vat

    def get_denominacionPartner(self, invoice):
        """
        Nombre del partner. Se obtiene del campo name del partner de la factura.
        :param invoice: record.
        :return: string, ej: 'Juan Bianchini'
        """
        return invoice.partner_id.name

    def get_importeTotal(self, invoice):
        """
        Devuelve el importe total de la factura
        :param invoice: record, factura.
        :return: string, monto ej: 5000->'500000' , 0->'0'
        """
        return self.helper.format_amount(self.rate * invoice.amount_total)

    def get_importeTotalNG(self, invoice):
        """
        Importe total de conceptos que no integran el precio neto gravado. Se obtienen a partir del campo
        amount_not_taxable.
        :param invoice: record.
        :return: string. ej: '12301'
        """
        return self.helper.format_amount(self.rate * invoice.amount_not_taxable)

    def get_importeOpExentas(self, invoice):
        """
        Devuelve el monto total de importes de operaciones exentas.
        :param invoice: record.
        :return: string, monto ej: 23.00-> '2300' 
        """
        return self.helper.format_amount(self.rate * invoice.amount_exempt)

    def get_importe_per_by_type(self, invoice, type):
        """
        Devuelve el monto total de percepciones de la factura de acuerdo al tipo de impuesto de percepcion.
        :param type: string, tipo de impuesto. ej: 'gross_income' (ingresos brutos)
        :param invoice: record.
        :return: string, monto ej: 23.00-> '2300'
        """
        importPer = sum(
            perception.amount
            if perception.perception_id.type == type
            else 0
            for perception in invoice.perception_ids
        )

        return self.helper.format_amount(self.rate * importPer)

    def get_importe_per_by_jurisdiction(self, invoice, jurisdiction):
        """
        Devuelve el monto total de percepciones de la factura de acuerdo al tipo de jurisdiccion de la percepcion.
        :param jurisdiction: string, ej 'municipal'
        :param invoice: record.
        :return: string, monto ej: '4500' 
        """
        importePer = sum(
            perception.amount
            if perception.perception_id.jurisdiction == jurisdiction
            else 0
            for perception in invoice.perception_ids
        )

        return self.helper.format_amount(self.rate * importePer)

    def get_importeImpInt(self, invoice):
        """
        Obtiene los impuestos internos de la factura formateados en string. 
        :param invoice: record.
        :return: string, monto ej: '2300' 
        """
        importeImpInt = sum(
            tax.amount
            if tax.tax_id.tax_group_id == self.data.tax_group_internal
            else 0
            for tax in invoice.tax_line_ids
        )
        return self.helper.format_amount(self.rate * importeImpInt)

    def get_codigoMoneda(self, invoice):
        """
        Obtiene el codigo de moneda de acuerdo a los mapeados en las tablas de AFIP
        Ejemplo: Las monedas Pesos y USD se mapean a PES y DOL.
        """
        return self.data.codes_model_proxy.get_code("res.currency", invoice.currency_id.id)

    def get_tipoCambio(self):
        """
        Este metodo obtiene el tipo de cambio, con las seis posiciones decimales que requiere el archivo,
        a partir del rate de la factura.
        """
        return self.helper.format_amount(self.rate, 6)

    def get_cantidadAlicIva(self, invoice):
        """
        Devuelve la cantidad de impuestos de la factura que pertenecen al grupo 'iva', o en su defecto devuelve 1.
        En caso de que la operacion sea exenta (E), se devuelve la cantidad de impuestos exentos.
        :param invoice: record.
        :return integer, ej: '3'
        """
        if self.get_codigoOperacion(invoice) == 'E':
            return len(self.get_invoice_exempt_taxes(invoice))

        # Se cuentan todos los impuestos que no son exentos, no gravados o sin impuestos.
        cantidadAlicIva = [
            tax for tax in invoice.tax_line_ids
            if tax.tax_id.tax_group_id == self.data.tax_group_vat
            and tax.tax_id != self.data.tax_purchase_ng
            and not tax.tax_id.is_exempt
        ]
        return len(cantidadAlicIva) or 1

    def get_alicuotaIva(self, tax):
        """
        Se devuelve el codigo de impuesto en base a las tablas de AFIP.
        :param tax: objeto impuesto
        :return integer, codigo de impuesto afip, ej: 5 
        """
        tax_code = self.data.codes_model_proxy.get_code(
            'account.tax',
            tax.tax_id.id
        )

        return tax_code

    def get_impuestoLiquidado(self, tax):
        """
        Devuelve el monto liquidado del impuesto.
        :param tax: record, impuesto.
        :return: string, monto del impuesto, ej:'1233'
        """
        return self.helper.format_amount(self.rate * tax.amount)

    def get_codigoOperacion(self, invoice):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. 
        -Si el total de impuestos menos los no gravados es igual a la cantidad de impuestos exentos, se
        califica la operacion como exenta.
        -Si el total de impuestos es igual al total de impuestos no gravados la operacion es no gravada.
        En caso de que la factura tenga 0 impuestos, la condicion dara verdadero y la operacion sera no gravada.
        -Actualmente no contempla el caso de importaciones
        de zona franca.
        :param invoice: record.
        :return string, ej 'N'
        """
        res = ''
        if invoice.denomination_id == self.data.type_d:
            res = 'X'

        exempt_taxes = self.get_invoice_exempt_taxes(invoice)
        not_taxed_taxes = self.get_invoice_notTaxed_taxes(invoice)
        other_taxes = self.get_invoice_other_taxes(invoice)

        if invoice.tax_line_ids and len(exempt_taxes) == len(invoice.tax_line_ids) - len(other_taxes):
            res = 'E'

        if invoice.tax_line_ids and len(not_taxed_taxes) == len(invoice.tax_line_ids) - len(other_taxes):
            res = 'N'

        return res

    def get_invoices_vat_taxes(self, invoice):
        exempt_taxes = self.get_invoice_exempt_taxes(invoice)
        not_taxed_taxes = self.get_invoice_notTaxed_taxes(invoice)

        if self.get_codigoOperacion(invoice) == 'E':
            return exempt_taxes

        elif self.get_codigoOperacion(invoice) == 'N':
            return not_taxed_taxes

        else:
            return invoice.tax_line_ids.filtered(
                lambda t: t.tax_id.tax_group_id == self.data.tax_group_vat
                and t not in set(exempt_taxes + not_taxed_taxes)
            )

    def get_invoice_notTaxed_taxes(self, invoice):
        raise NotImplementedError

    def get_invoice_other_taxes(self, invoice):
        return [
            tax for tax in invoice.tax_line_ids
            if tax.tax_id.tax_group_id != self.data.tax_group_vat
        ]

    def get_otrosTrib(self, invoice):
        """
        Devuelve la suma de todos los impuestos que NO son internos, de iva, percepciones,
        en formato string.
        :param invoice: record.
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
        return self.helper.format_amount(self.rate * otrosTrib)

    @staticmethod
    def get_invoice_exempt_taxes(invoice):
        return [
            tax for tax in invoice.tax_line_ids
            if tax.tax_id.is_exempt
        ]


class PurchasePresentation(Presentation):
    # ----------------CAMPOS COMPRAS----------------
    def get_puntoDeVenta(self, invoice):
        """
        Si la denominacion de la factura es tipo D, se devuelve vacio.
        :param invoice: record.
        :return: string, ej: '0001'
        """
        if invoice.denomination_id == self.data.type_d:
            return ''
        return super(PurchasePresentation, self).get_puntoDeVenta(invoice)

    def get_numeroComprobante(self, invoice):
        """
        Si la denominacion de la factura es tipo D, se devuelve vacio.
        :param invoice: record.
        :return: string, ej: '11110001'
        """
        if invoice.denomination_id == self.data.type_d:
            return ''
        return super(PurchasePresentation, self).get_numeroComprobante(invoice)

    def get_despachoImportacion(self, invoice):
        """
        Si la denominacion de la factura es D, devolvemos el numero de la factura
        que es el despacho de importacion.
        :param invoice: record.
        :return string, despacho de importacion. ej: '17HB1A73G008'
        """
        if invoice.denomination_id != self.data.type_d:
            return ''
        return invoice.name

    def get_invoice_notTaxed_taxes(self, invoice):
        return [
            tax for tax in invoice.tax_line_ids
            if tax.tax_id == self.data.tax_purchase_ng
        ]


class PurchaseVatPresentation(PurchasePresentation):

    def get_importeNetoGravado(self, tax):
        """
        Obtiene el neto gravado de la operacion. Para los impuestos exentos o no gravados devuelve 0.
        :param tax: objeto impuesto
        :return: string, monto del importe
        """
        if tax.tax_id.is_exempt or tax.tax_id == self.data.tax_purchase_ng:
            return '0'
        return self.helper.format_amount(tax.base * self.rate)


class SalePresentation(Presentation):

    def get_invoice_notTaxed_taxes(self, invoice):
        return [
            tax for tax in invoice.tax_line_ids
            if tax.tax_id == self.data.tax_sale_ng
        ]


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
