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

class PurchaseImportationPresentation:
    def __init__(self, helper, builder, data, purchase_presentation, purchase_iva_presentation):
        self.helper = helper
        self.builder = builder
        self.data = data
        self.purchase_presentation = purchase_presentation
        self.purchase_iva_presentation = purchase_iva_presentation

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de alicuotas de compras de importacion.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ['in_invoice', 'in_refund']
                      and i.denomination_id in [self.data.type_d]
        )

    def generate(self, invoices):
        filtered_invoices = self.filter_invoices(invoices)
        map(lambda invoice: self.create_line(invoice), filtered_invoices)
        return self.builder

    def create_line(self, invoice):
        """
        Crea x lineas por cada factura, segun la cantidad de alicuotas usando el builder y el helper
        para todas las facturas de importacion.
        :param builder: objeto de la api para construir las lineas de la presentacion
        :param invoice: record, factura
        :param helper: objeto con metodos auxiliares
        """

        for tax in invoice.tax_line_ids:
            if tax.tax_id.tax_group_id == self.data.tax_group_vat:
                importation_line = self.builder.create_line()
                rate = self.helper.get_currency_rate_from_move(invoice)

                importation_line.despachoImportacion = self.purchase_presentation.get_purchase_despachoImportacion(invoice)
                importation_line.importeNetoGravado = self.purchase_iva_presentation.get_purchase_vat_importeNetoGravado(tax, rate)
                importation_line.alicuotaIva = self.purchase_iva_presentation.get_purchase_vat_alicuotaIva(tax)
                importation_line.impuestoLiquidado = self.helper.format_amount(rate * tax.amount)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
