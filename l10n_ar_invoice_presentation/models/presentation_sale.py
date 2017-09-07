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

    def create_line(self, builder, invoice, helper, codes_proxy):
        """
        Crea una linea por cada factura, usando el builder y el helper
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """
        line = builder.create_line()
        # campo 1: fecha de comprobante
        line.fecha = self.get_fecha(invoice, helper)
        # campo 2: tipo de comprobante
        line.tipo = self.get_tipo(invoice, helper)
        # campo 3: punto de Venta
        line.puntoDeVenta = self.get_punto_venta(invoice)
        # campo 4: numero de comprobante
        line.numeroComprobante = self.get_numero_comprobante(invoice)
        # campo 5: numero de comprobante hasta
        line.numeroHasta = self.get_numero_comprobante(invoice)
        # campo 6: codigo de documento del comprador
        line.codigoDocumento = self.get_codigo_documento(invoice, codes_proxy)
        # campo 7: numero de identificacion del comprador
        line.numeroComprador = self.get_numero_comprador(invoice)
        # campo 8: apellido y nombre del comprador
        line.denominacionComprador = self.get_denominacion_comprador(invoice)
        # campo 9: importe total de la operacion
        line.importeTotal = self.get_importe_total(invoice, helper)
        # campo 10: importe total de conceptos que no integran el precio neto gravado
        line.importeTotalNG = self.get_importe_total_ng(invoice, helper)
        # campo 11: percepcion a no categorizados
        line.percepcionNC = self.get_percepcion_nc(invoice, helper)
        # campo 12: importe de operaciones exentas
        line.importeExentos = self.get_importe_exentos(invoice, helper)
        # campo 13: importe de percepciones o pagos a cuenta de impuestos nacionales
        line.importePercepciones = self.get_importe_percepciones(invoice, helper)
        # campo 14: importe de percepciones de ingresos brutos
        line.importePerIIBB = self.get_importe_per_iibb(invoice, helper)
        # campo 15: importe de percepciones de impuestos municipales
        line.importePerIM = self.get_importe_per_im(invoice, helper)
        # campo 16: importe de impuestos internos
        line.importeImpInt = self.get_importe_imp_int(invoice, helper)
        # campo 17: codigo de moneda
        line.codigoMoneda = self.get_codigo_moneda(invoice, codes_proxy)
        # campo 18: tipo de cambio
        line.tipoCambio = self.get_tipo_cambio(invoice, helper)
        # campo 19: cantidad de alicuotas de IVA
        line.cantidadAlicIva = self.get_cantidad_alic_iva(invoice)
        # campo 20: codigo de operacion
        line.codigoOperacion = self.get_codigo_operacion(invoice)
        # campo 21: otros tributos
        line.otrosTributos = self.get_otros_tributos(invoice, helper)
        # campo 22: fecha de vencimiento de pago
        line.fechaVtoPago = self.get_fecha_vto_pago(invoice, helper)

    @staticmethod
    def get_fecha(invoice, helper):
        """
        Campo 1: Fecha de comprobante.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La fecha de comprobante.
        """
        return helper.format_date(invoice.date_invoice)

    @staticmethod
    def get_tipo(invoice, helper):
        """
        Campo 2: Tipo de comprobante.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El tipo de comprobante.
        """
        return helper.get_invoice_type(invoice)

    @staticmethod
    def get_punto_venta(invoice):
        """
        Campo 3: Punto de venta.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: El punto de venta.
        """
        return invoice.name[0:4]

    @staticmethod
    def get_numero_comprobante(invoice):
        """
        Campo 4: Numero de comprobante.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: El numero de comprobante.
        """
        return invoice.name[-8:]

    @staticmethod
    def get_codigo_documento(invoice, codes_proxy):
        """
        Campo 6: Codigo de documento del comprador.
        :param invoice: La factura de la cual se sacara la informacion.
        :param codes_proxy: El proxy de `codes.models.relation`.
        :return: El codigo de documento del comprador.
        """
        codigo_documento = codes_proxy.get_code(
            "partner.document.type",
            invoice.partner_id.partner_document_type_id.id
        )
        return codigo_documento

    @staticmethod
    def get_numero_comprador(invoice):
        """
        Campo 7: Numero de identificacion del comprador.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: El numero de identificacion del comprador.
        """
        return invoice.partner_id.vat

    @staticmethod
    def get_denominacion_comprador(invoice):
        """
        Campo 8: Apellido y nombre del comprador.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: El apellido y nombre del comprador.
        """
        return invoice.partner_id.name

    @staticmethod
    def get_importe_total(invoice, helper):
        """
        Campo 9: Importe total de la operacion.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe total de la operacion.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_total
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_total_ng(invoice, helper):
        """
        Campo 10: Importe total de conceptos que no integran el precio neto gravado.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe total de conceptos que no integran el precio neto gravado.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_not_taxable
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_percepcion_nc(invoice, helper):
        """
        Campo 11: Percepcion a no categorizados.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La percepcion a no categorizados.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = sum(
            invoice.perception_ids.filtered(
                lambda p: not p.perception_id.jurisdiction
            ).mapped("amount")
        )
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_exentos(invoice, helper):
        """
        Campo 12: Importe de operaciones exentas.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe de operaciones exentas.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = invoice.amount_exempt
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_percepciones(invoice, helper):
        """
        Campo 13: Importe de percepciones o pagos a cuenta de impuestos nacionales.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe de percepciones o pagos a cuenta de impuestos nacionales.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = sum(
            invoice.perception_ids.filtered(
                lambda p: p.perception_id.jurisdiction == "nacional"
            ).mapped("amount")
        )
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_per_iibb(invoice, helper):
        """
        Campo 14: Importe de percepciones de ingresos brutos.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe de percepciones de ingresos brutos.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = sum(
            invoice.perception_ids.filtered(
                lambda p: p.perception_id.jurisdiction == "provincial"
            ).mapped("amount")
        )
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_per_im(invoice, helper):
        """
        Campo 15: Importe de percepciones de impuestos municipales.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe de percepciones de impuestos municipales.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        amount = sum(
            invoice.perception_ids.filtered(
                lambda p: p.perception_id.jurisdiction == "municipal"
            ).mapped("amount")
        )
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_importe_imp_int(invoice, helper):
        """
        Campo 16: Importe de impuestos internos.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El importe de impuestos internos.
        """
        tax_group_internal = invoice.env.ref("l10n_ar.tax_group_internal")
        rate = helper.get_currency_rate_from_move(invoice)
        amount = .0
        for tax in invoice.tax_line_ids:
            amount += tax.amount if tax.tax_id.tax_group_id.id == tax_group_internal.id else .0
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_codigo_moneda(invoice, codes_proxy):
        """
        Campo 17: Codigo de moneda.
        :param invoice: La factura de la cual se sacara la informacion.
        :param codes_proxy: El proxy de `codes.models.relation`.
        :return: El codigo de moneda.
        """
        model_name = "res.currency"
        model_id = invoice.currency_id.id
        return codes_proxy.get_code(model_name, model_id)

    @staticmethod
    def get_tipo_cambio(invoice, helper):
        """
        Campo 18: Tipo de cambio.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: El tipo de cambio
        """
        rate = helper.get_currency_rate_from_move(invoice)
        return helper.format_amount(rate, 6)

    @staticmethod
    def get_cantidad_alic_iva(invoice):
        """
        Campo 19: Cantidad de alicuotas de IVA.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: La cantidad de alicuotas de IVA.
        """
        # Traemos cantidad de impuestos exentos
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if len(exempt_taxes) == len(invoice.tax_line_ids):
            return 1
        cantidad_alic_iva = 0
        tax_group_vat = invoice.env.ref("l10n_ar.tax_group_vat")
        for tax in invoice.tax_line_ids:
            cantidad_alic_iva += 1 if tax.tax_id.tax_group_id == tax_group_vat else 0
        return cantidad_alic_iva or 1

    @staticmethod
    def get_codigo_operacion(invoice):
        """
        Campo 20: Codigo de operacion.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: El codigo de operacion.
        """
        codigo_operacion = " "
        # Exento:
        # Si el total de impuestos es igual al total de impuestos exentos
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if len(exempt_taxes) == len(invoice.tax_line_ids):
            codigo_operacion = "E"
        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados
        not_taxed_tax_id = invoice.env.ref("l10n_ar.1_vat_no_gravado_ventas")
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == not_taxed_tax_id]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            codigo_operacion = "N"
        # IMPORTACIONES
        type_d = invoice.env.ref("l10n_ar_afip_tables.account_denomination_d")
        # Exportaciones:
        # Si tiene despacho de importacion y este viene directo de aduana
        if invoice.denomination_id == type_d:
            codigo_operacion = "X"
            # Importaciones de zona franca
            # Si tiene despacho de importacion y este viene de zona franca
            ar_country = invoice.env.ref("base.ar")
            if invoice.partner_id.country_id == ar_country:
                codigo_operacion = "Z"
        return codigo_operacion

    @staticmethod
    def get_otros_tributos(invoice, helper):
        """
        Campo 21: Otros tributos.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: Los otros tributos.
        """
        not_other_tax_group_ids = [
            invoice.env.ref('l10n_ar.tax_group_internal'),
            invoice.env.ref('l10n_ar.tax_group_vat'),
            invoice.env.ref('l10n_ar_retentions.tax_group_retention'),
            invoice.env.ref('l10n_ar_perceptions.tax_group_perception'),
        ]
        rate = helper.get_currency_rate_from_move(invoice)
        amount = .0
        for tax in invoice.tax_line_ids:
            amount += tax.amount if tax.tax_id.tax_group_id not in not_other_tax_group_ids else .0
        return helper.format_amount(rate * amount)

    @staticmethod
    def get_fecha_vto_pago(invoice, helper):
        """
        Campo 22: Fecha de vencimiento de pago.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La fecha de vencimiento de pago.
        """
        type_e = invoice.env.ref("l10n_ar_afip_tables.account_denomination_e")
        ret = "".zfill(8)
        if invoice.denomination_id.id != type_e.id:
            ret = helper.format_date(invoice.date_due)
        return ret


class AccountInvoicePresentation(models.Model):
    _inherit = "account.invoice.presentation"

    def generate_sale_file(self):
        """
        Se genera el archivo de ventas. Utiliza la API de presentaciones y tools para poder crear los archivos
        y formatear los datos.
        :return: objeto de la api (generator), con las lineas de la presentacion creadas.
        """
        # instanciamos el builder de la api
        builder = presentation_builder.Presentation("ventasCompras", "ventasCbte")
        # instanciamos las tools de ventas-compras
        helper = PresentationTools()
        # Instanciamos la clase ayudadora xD de la presentacion puntual que estamos haciendo
        presentation = SaleInvoicePresentation()
        # escribimos las propiedades de SaleAccountInvoicePresentation
        presentation.invoice_proxy = self.env["account.invoice"]
        presentation.invoice_date_from = self.date_from
        presentation.invoice_date_to = self.date_to
        # se traen todas las facturas de venta del periodo indicado
        invoices = presentation.get_invoices()
        # validamos que tengan los datos necesarios
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
