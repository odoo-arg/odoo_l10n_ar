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
    def __init__(self, invoice_proxy=None, date_from=None, date_to=None, helper=None):
        self.invoice_proxy = invoice_proxy
        self.invoice_date_from = date_from
        self.invoice_date_to = date_to
        self.helper = helper
        self.get_general_data()

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

    # Datos del sistema
    def get_general_data(self):
        """
        Obtiene valores predeterminados de la localizacion
        """
        self.type_b = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_b')
        self.type_c = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_c')
        self.type_d = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_d')
        self.type_i = self.invoice_proxy.env.ref('l10n_ar_afip_tables.account_denomination_i')
        self.tax_group_vat = self.invoice_proxy.env.ref('l10n_ar.tax_group_vat')

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
        # Campos 11, 13, 14 y 15 (Percepciones)
        self.fill_perceptions(invoice,helper,line)
        # campo 12: importe de operaciones exentas
        line.importeExentos = self.get_importe_exentos(invoice, helper)
        # campo 16: importe de impuestos internos
        line.importeImpInt = self.get_importe_imp_int(invoice, helper)
        # campo 17: codigo de moneda
        line.codigoMoneda = self.get_codigo_moneda(invoice, codes_proxy)
        # campo 18: tipo de cambio
        line.tipoCambio = self.get_tipo_cambio(invoice, helper)
        # campo 19: cantidad de alicuotas de IVA
        line.cantidadAlicIva = self.get_cantidad_alic_iva(invoice, self.tax_group_vat)
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

    def fill_perceptions(self,invoice,helper,line):
        no_categorizado = invoice.env.ref('l10n_ar_afip_tables.account_fiscal_position_no_categ')
        if invoice.partner_id.property_account_position_id == no_categorizado:
            line.percepcionNC = self.get_percepcion_nc(invoice,helper)
        else:
            line.importePercepciones = self.get_importe_percepciones(invoice,helper)
            line.importePerIIBB = self.get_importe_per_iibb(invoice,helper)
            line.importePerIM = self.get_importe_per_im(invoice,helper)

    @staticmethod
    def get_percepcion_nc(invoice, helper):
        """
        Campo 11: Percepcion a no categorizados.
        :param invoice: La factura de la cual se sacara la informacion.
        :param helper: Las presentation tools.
        :return: La percepcion a no categorizados.
        """
        rate = helper.get_currency_rate_from_move(invoice)
        no_categorizado = invoice.env.ref('l10n_ar_afip_tables.account_fiscal_position_no_categ')
        amount = sum(invoice.perception_ids.mapped("amount"))\
            if invoice.partner_id.property_account_position_id == no_categorizado \
            else 0
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
                lambda p: p.perception_id.type == "gross_income"
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
    def get_cantidad_alic_iva(invoice, tax_group_vat):
        """
        Campo 19: Cantidad de alicuotas de IVA.
        :param invoice: La factura de la cual se sacara la informacion.
        :return: La cantidad de alicuotas de IVA.
        """
        # Traemos impuestos exentos que no son no gravados
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]

        # Traemos impuestos no gravados (tipo de impuesto 'no gravado')
        tax_compras_ng = invoice.env.ref('l10n_ar.1_vat_no_gravado_compras')
        untaxable_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == tax_compras_ng]
        # Si la cantidad de exentos es igual a la cantidad total sin los no gravados, devolvemos exentos
        if len(exempt_taxes) == len(invoice.tax_line_ids) - len(untaxable_taxes):
            return len(exempt_taxes) or 1

        # En caso contrario devolvemos la cantidad de alicuotas de iva restantes, o 1
        cantidadAlicIva = [tax for tax in invoice.tax_line_ids if tax.tax_id.tax_group_id == tax_group_vat]
        return len(cantidadAlicIva) if len(cantidadAlicIva) > 0 else 1

    @staticmethod
    def get_codigo_operacion(invoice):
        """
        Obtiene el codigo de operacion de acuerdo a los impuestos. Solo si la alicuota de iva es 0.
        de zona franca.
        """
        if SaleInvoicePresentation.get_cantidad_alic_iva(invoice) != 0:
            return ''
        # Exento:
        # Si el total de impuestos es igual al total de impuestos exentos la operacion es exenta.
        exempt_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id.is_exempt]
        if invoice.tax_line_ids and len(exempt_taxes) == len(invoice.tax_line_ids):
            return 'E'

        # No gravado:
        # Si el total de impuestos es igual al total de impuestos no gravados la operacion es no gravada.
        # En caso de que la factura tenga 0 impuestos, la condicion dara verdadero y la operacion sera no gravada.
        not_taxed_tax_id = invoice.env.ref('l10n_ar.1_vat_no_gravado_ventas')
        not_taxed_taxes = [tax for tax in invoice.tax_line_ids if tax.tax_id == not_taxed_tax_id]
        if len(not_taxed_taxes) == len(invoice.tax_line_ids):
            return 'N'

        # Exportacion:
        # Si el partner tiene como posicion fiscal 'despachante de aduana' la operacion es de exportacion
        fiscal_position_ad = invoice.env.ref("l10n_ar_afip_tables.account_fiscal_position_despachante_aduana")
        if invoice.partner_id.property_account_position_id == fiscal_position_ad:
            return 'X'

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
        # Instanciamos helper de la presentacion puntual que estamos haciendo
        presentation = SaleInvoicePresentation(
            invoice_proxy = self.env["account.invoice"],
            date_from = self.date_from,
            date_to = self.date_to,
            helper=helper
        )
        # se traen todas las facturas de venta del periodo indicado
        invoices = presentation.get_invoices()
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
