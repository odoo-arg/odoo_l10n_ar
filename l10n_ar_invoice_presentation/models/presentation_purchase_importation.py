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
from presentation_purchase_iva import PurchaseIvaPresentation


class PurchaseImportationPresentation(PurchaseIvaPresentation):
    def __init__(self, builder, data):
        super(PurchaseImportationPresentation, self).__init__(builder, data)

    def filter_invoices(self, invoices):
        """
        Trae las facturas para generar la presentacion de alicuotas de compras de importacion.
        :return: recordset, Las facturas de compras.
        """
        return invoices.filtered(
            lambda i: i.type in ['in_invoice', 'in_refund']
                      and i.denomination_id in [self.data.type_d]
        )

    def create_line(self, invoice):
        """
        Crea x lineas por cada factura, segun la cantidad de alicuotas usando el builder y el helper
        para todas las facturas de importacion.
        :param invoice: record, factura
        """
        self.rate = self.helper.get_currency_rate_from_move(invoice)

        for tax in invoice.tax_line_ids:
            if tax.tax_id.tax_group_id == self.data.tax_group_vat:
                importation_line = self.builder.create_line()

                importation_line.despachoImportacion = self.get_despachoImportacion(invoice)
                importation_line.importeNetoGravado = self.get_importeNetoGravado(tax)
                importation_line.alicuotaIva = self.get_alicuotaIva(tax)
                importation_line.impuestoLiquidado = self.helper.format_amount(self.rate * tax.amount)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
