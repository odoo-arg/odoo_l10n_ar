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
    def __init__(self, proxy=None, date_from=None, date_to=None, with_prorate=False):
        self.invoice_proxy = proxy
        self.date_from = date_from
        self.date_to = date_to
        self.with_prorate = with_prorate
        self.get_general_data()

    # Datos del sistema
    def get_general_data(self):
        "Obtiene valores predeterminados de la localizacion"
        self.type_b = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_b')
        self.type_c = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_c')
        self.type_d = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_d')
        self.type_i = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_i')
        self.tax_group_vat = self.invoice_proxy.env.ref('l10n_ar.tax_group_vat')

    def get_invoices(self):
        """
        Trae las facturas para generar la presentacion de compras.
        :return: recordset, Las facturas de compras.
        """
        invoices = self.invoice_proxy.search([
            ('type', 'in', ('in_invoice', 'in_refund')),
            ('state', 'not in', ('cancel', 'draft')),
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to),
            ('denomination_id', '!=', self.type_i.id)
        ])
        return invoices
    
    def create_line(self, builder, invoice, helper):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        line = builder.create_line()

        line.fecha = self.get_purchase_fecha(invoice, helper)
        line.tipo = self.get_purchase_tipo(invoice, helper)
        line.puntoDeVenta = self.get_purchase_puntoDeVenta(invoice, self.type_d)
        line.numeroComprobante = self.get_purchase_numeroComprobante(invoice, self.type_d)
        line.despachoImportacion = self.get_purchase_despachoImportacion(invoice, self.type_d)
        line.codigoDocumento = self.get_purchase_codigoDocumento(invoice)
        line.numeroVendedor = self.get_purchase_numeroVendedor(invoice)
        line.denominacionVendedor = self.get_purchase_denominacionVendedor(invoice)
        line.importeTotal = self.get_purchase_importeTotal(invoice, helper)
        line.importeTotalNG = self.get_purchase_importeTotalNG(invoice, helper, self.get_purchase_codigoOperacion(invoice, self.type_d))
        line.importeOpExentas = self.get_purchase_importeOpExentas(invoice, helper)
        line.importePerOIva = self.get_purchase_importePerOIva(invoice, helper)
        line.importePerOtrosImp = self.get_purchase_importePerOtrosImp(invoice, helper)
        line.importePerIIBB = self.get_purchase_importePerIIBB(invoice, helper)
        line.importePerIM = self.get_purchase_importePerIM(invoice, helper)
        line.importeImpInt = self.get_purchase_importeImpInt(invoice, helper)
        line.codigoMoneda = self.get_purchase_codigoMoneda(invoice)
        line.tipoCambio = self.get_purchase_tipoCambio(invoice, helper)
        line.cantidadAlicIva = self.get_purchase_cantidadAlicIva(invoice, self.type_b, self.type_c, self.tax_group_vat)
        line.codigoOperacion = self.get_purchase_codigoOperacion(invoice, self.type_d)
        line.credFiscComp = self.get_purchase_credFiscComp(invoice, helper, self.type_b, self.type_c, self.tax_group_vat, self.with_prorate)
        line.otrosTrib = self.get_purchase_otrosTrib(invoice, helper)
        line.cuitEmisor = self.get_purchase_cuitEmisor()
        line.denominacionEmisor = self.get_purchase_denominacionEmisor()
        line.ivaComision = self.get_purchase_ivaComision()

    # ----------------CAMPOS COMPRAS----------------
    # Campo 1
    @staticmethod
    def get_purchase_fecha(invoice, helper):
        return helper.format_date(invoice.date_invoice)

    # Campo 2
    @staticmethod
    def get_purchase_tipo(invoice, helper):
        return helper.get_invoice_type(invoice)

    # Campo 3
    @staticmethod
    def get_purchase_puntoDeVenta(invoice, type_d):
        if invoice.denomination_id == type_d:
            return ''
        return invoice.name[0:4]

    # Campo 4
    @staticmethod
    def get_purchase_numeroComprobante(invoice, type_d):
        if invoice.denomination_id == type_d:
            return ''
        return invoice.name[-8:]

    # Campo 5
    @staticmethod
    def get_purchase_despachoImportacion(invoice, type_d):
        """Si la denominacion de la factura es D, devolvemos el numero de la factura
        que es el despacho de importacion"""
        if invoice.denomination_id != type_d:
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
    @staticmethod
    def get_purchase_importeTotal(invoice, helper):
        """
        Devuelve el importe total de la factura
        :param invoice: record, factura.
        :param helper: instancia de PresentationTools, con herramientas de formateo.
        :return: string, monto ej: 5000->'500000' , 0->'0'
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_total
        return helper.format_amount(rate * amount)

    # Campo 10
    @staticmethod
    def get_purchase_importeTotalNG(invoice, helper, cod_ope):
        """
        Devuelve el importe total no gravado. Si el importe total de la operacion es 'N' devuelve 0.
        :param cod_ope: Codigo de operacion. ej: 'N'   
        :return: string, monto ej: 23.00-> '2300' , 0->'0'
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = 0 if cod_ope == 'N' else invoice.amount_not_taxable
        return helper.format_amount(rate * amount)

    # Campo 11
    @staticmethod
    def get_purchase_importeOpExentas(invoice, helper):
        """
        Devuelve el monto total de importes de operaciones exentas.
        :return: string, monto ej: 23.00-> '2300' 
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_exempt

        return helper.format_amount(rate * amount)

    # Campo 12
    @staticmethod
    def get_purchase_importePerOIva(invoice, helper):
        """
        Devuelve el monto total de percepciones de iva de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """
        importPerOIva = 0.00
        for perception in invoice.perception_ids:
            importPerOIva += perception.amount if perception.perception_id.type == 'vat' else 0

        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * importPerOIva)

    # Campo 13
    @staticmethod
    def get_purchase_importePerOtrosImp(invoice, helper):
        """
        Devuelve el monto total de percepciones de otros impuestos de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """
        importePerOtrosImp = 0.00
        for perception in invoice.perception_ids:
            importePerOtrosImp += perception.amount if perception.perception_id.type == 'other' else 0

        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * importePerOtrosImp)

    # Campo 14
    @staticmethod
    def get_purchase_importePerIIBB(invoice, helper):
        """
        Devuelve el monto total de percepciones de ingresos brutos de la factura.
        :return: string, monto ej: 23.00-> '2300'
        """
        importePerIIBB = 0.00
        for perception in invoice.perception_ids:
            importePerIIBB += perception.amount if perception.perception_id.type == 'gross_income' else 0
        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * importePerIIBB)

    # Campo 15
    @staticmethod
    def get_purchase_importePerIM(invoice, helper):
        """
        Devuelve el monto total de percepciones de impuestos municipales de la factura.
        :return: string, monto ej: '4500' 
        """
        importePerIM = 0.00
        for perception in invoice.perception_ids:
            importePerIM += perception.amount if perception.perception_id.jurisdiction == 'municipal' else 0

        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * importePerIM)

    # Campo 16
    @staticmethod
    def get_purchase_importeImpInt(invoice, helper):
        """
        Obtiene los impuestos internos de la factura formateados en string. 
        :return: string, monto ej: '2300' 
        """
        importeImpInt = 0.00
        tax_group_internal = invoice.env.ref('l10n_ar.tax_group_internal')
        for tax in invoice.tax_line_ids:
            importeImpInt += tax.amount if tax.tax_id.tax_group_id == tax_group_internal else 0
        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * importeImpInt)

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
    @staticmethod
    def get_purchase_tipoCambio(invoice, helper):
        "Este metodo obtiene el tipo de cambio, con las seis posiciones decimales que requiere el archivo."
        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate, 6)

    # Campo 19
    @staticmethod
    def get_purchase_cantidadAlicIva(invoice, type_b, type_c, tax_group_vat):
        """
        En caso de ser comprobante B o C se devuelve 0. En caso de que todos los impuestos sean
        exentos, devolver 1. En caso de que haya una o mas alicuotas de iva no exentas se devuelve 
        la cantidad. En el resto de los casos se devuelve 1.
        """
        if invoice.denomination_id in [type_b, type_c]:
            return 0

        # Traemos cantidad de impuestos exentos
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if len(exempt_taxes) == len(invoice.tax_line_ids):
            return 1

        cantidadAlicIva = 0
        for tax in invoice.tax_line_ids:
            cantidadAlicIva += 1 if tax.tax_id.tax_group_id == tax_group_vat else 0

        return cantidadAlicIva if cantidadAlicIva > 0 else 1

    # Campo 20
    @staticmethod
    def get_purchase_codigoOperacion(invoice, type_d):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. Actualmente no contempla el caso de importaciones
        de zona franca.
        """
        codigoOperacion = ' '

        # Exento:
        # Si el total de impuestos es igual al total de impuestos exentos
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if len(exempt_taxes) == len(invoice.tax_line_ids):
            codigoOperacion = 'E'

        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados
        not_taxed_tax_id = invoice.env.ref('l10n_ar.1_vat_no_gravado_compras')
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == not_taxed_tax_id]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            codigoOperacion = 'N'

        # IMPORTACIONES
        # Importaciones del exterior:
        # Si tiene despacho de importacion y este viene directo de aduana
        if invoice.denomination_id == type_d:
            codigoOperacion = 'X'

        return codigoOperacion

    # Campo 21
    @staticmethod
    def get_purchase_credFiscComp(invoice, helper, type_b, type_c, tax_group_vat, with_prorate):
        """
        Se devuelve cero en caso de que no tenga alicuotas de iva. Si tiene alicuotas y la presentacion es
        sin prorrateo, se devuelven todos los impuestos. En caso contrario se devuelve la suma de los impuestos
        de iva.
        """
        # Si la cantidad de alicuotas es igual a 0, se devuelve 0
        if PurchaseInvoicePresentation.get_purchase_cantidadAlicIva(invoice, type_b, type_c, tax_group_vat) is 0:
            return 0

        # Si es sin prorrateo , se devuelve el total de impuestos liquidado
        rate = helper.get_currency_rate_from_move(invoice)
        if not with_prorate:
            return helper.format_amount(invoice.amount_tax * rate)
        # Sino se devuelve el monto de los impuestos de iva
        else:
            vat_tax_amount = sum(
                invoice.tax_line_ids.filtered(lambda t: t.tax_id.tax_group_id == tax_group_vat).mapped(
                    'amount'))
            return helper.format_amount(vat_tax_amount * rate)

    # Campo 22
    @staticmethod
    def get_purchase_otrosTrib(invoice, helper):
        """
        Devuelve la suma de todos los impuestos que NO son internos, de iva, retenciones o percepciones,
        en formato string
        :return: string, monto formateado. ej: '223455'
        """
        otrosTrib = 0.00
        tax_group_ids = [
            invoice.env.ref('l10n_ar.tax_group_internal'),
            invoice.env.ref('l10n_ar.tax_group_vat'),
            invoice.env.ref('l10n_ar_retentions.tax_group_retention'),
            invoice.env.ref('l10n_ar_perceptions.tax_group_perception'),
        ]
        for tax in invoice.tax_line_ids:
            otrosTrib += tax.amount if tax.tax_id.tax_group_id not in tax_group_ids else 0
        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate * otrosTrib)

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
        helper = PresentationTools()
        presentation = PurchaseInvoicePresentation(
            proxy=self.env["account.invoice"],
            date_from=self.date_from,
            date_to=self.date_to,
            with_prorate=self.with_prorate
        )

        # Se traen todas las facturas de compra del periodo indicado
        invoices = presentation.get_invoices()
        # Validamos que se tengan los datos necesarios de los partners.
        self.validate_invoices(invoices)

        # Se crea la linea de la presentacion para cada factura.
        map(
            lambda invoice: presentation.create_line(
                builder, invoice, helper
            ), invoices
        )
        return builder


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
