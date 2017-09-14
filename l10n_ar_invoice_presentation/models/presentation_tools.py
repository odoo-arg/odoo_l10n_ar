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

class PresentationTools:
    def __init__(self):
        pass

    @staticmethod
    def get_invoices(self, domain, date_from, date_to):
        invoices = self.invoice_proxy.search([
            ('type', 'in', ('in_invoice', 'in_refund')),
            ('state', 'not in', ('cancel', 'draft')),
            ('date_invoice', '>=', self.date_from),
            ('date_invoice', '<=', self.date_to),
            ('denomination_id', '!=', self.type_i.id)
        ])
        return invoices

    @staticmethod
    def format_date(d):
        # type: (str) -> str
        """
        Formatea la fecha para su presentacion en ventas compras.
        :param d: La fecha a formatear.
        :type d: str
        :return: La fecha formateada.
        :rtype: str
        """
        if not isinstance(d, str):
            d = str(d)
        return d.replace("-", "")

    @staticmethod
    def get_currency_rate_from_move(invoice):
        """
        Obtiene la currency de la factura, a partir de las lineas del asiento.
        :param invoice: record, factura
        :return: float, currency. ej: 15.32
        """
        move = invoice.move_id
        account = invoice.account_id

        # Traemos todas las lineas del asiento que tengan esa cuenta
        move_line = move.line_ids.filtered(lambda x: x.account_id == account)[0]

        # Traemos el monto de la linea, si es de debito o credito
        amount = move_line.credit or move_line.debit
        amount_currency = abs(move_line.amount_currency)
        # El rate sera el monto dividido la currency si es distinto de cero, sino se divide por si mismo
        currency_rate = float(amount) / float(amount_currency or amount)

        return currency_rate

    @staticmethod
    def get_invoice_type(invoice):
        """
        Obtiene el tipo de factura, a partir de los codigos de AFIP.
        :param invoice: record, factura
        :return: string, codigo de afip del tipo de factura
        """
        # Guardamos en invoice_type si es nota de debito, credito o factura
        if invoice.is_debit_note:
            invoice_type = 'debit_note'
        else:
            invoice_type = 'invoice' if invoice.type in ['out_invoice', 'in_invoice'] else 'refund'

        # Buscamos el tipo de talonario segun el tipo de factura
        document_type_id = invoice.env['document.book.document.type'].search([
            ('type', '=', invoice_type),
            ('category', '=', 'invoice'),
        ], limit=1)
        # Buscamos el tipo de voucher almacenado en sistema de acuerdo al tipo de talonario y denominacion
        # TODO: Para los despachos de importacion el voucher type no va a existir por un problema de mapeo
        # El siguiente bloque if/else es temporal y debe ser removido.
        type_i = invoice.env.ref('l10n_ar_afip_tables.account_denomination_i')
        if invoice.denomination_id == invoice.env.ref('l10n_ar_afip_tables.account_denomination_d'):
            voucher_type = invoice.env['afip.voucher.type'].search([
                ('document_type_id', '=', document_type_id.id),
                ('denomination_id', '=', type_i.id)],
                limit=1
            )
        else:
            # Conservar solo esta porcion de codigo
            voucher_type = invoice.env['afip.voucher.type'].search([
                ('document_type_id', '=', document_type_id.id),
                ('denomination_id', '=', invoice.denomination_id.id)],
                limit=1
            )
        # Traemos el codigo de afip de la tabla de relaciones, en base a lo antes calculado
        document_afip_code = int(invoice.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))

        return document_afip_code

    @staticmethod
    def format_amount(amount, dp=2):
        # type: (float, int) -> str
        """
        Formatea el numero con la cantidad de decimales que se le pase, o dos decimales por defecto.
        :param amount: El numero a formatear.
        :type amount: float
        :param dp: La precision decimal, a.k.a. la cantidad de decimales.
        :type dp: int
        :return: El numero formateado a string.
        :rtype: str
        """
        amount = str("{0:.{1}f}".format(amount, dp))
        amount = amount.replace(".", "").replace(",", "")
        return amount

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
