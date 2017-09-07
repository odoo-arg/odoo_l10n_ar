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
        # traemos el poxy
        account_move_line_proxy = invoice.env["account.move.line"]
        # sacamos el move de la factura
        move = invoice.move_id
        # sacamos la cuenta de la factura
        account = invoice.account_id
        # buscamos las move lines que pertenezcan al move y a la cuenta de la factura
        move_line = account_move_line_proxy.search(
            [
                ("move_id", "=", move.id),
                ("account_id", "=", account.id)
            ],
            limit=1
        )
        # traemos el credito o debito de la move line
        amount = move_line.credit or move_line.debit
        # traemos el monto moneda
        amount_currency = abs(move_line.amount_currency)
        # calculamos el rate de la moneda
        currency_rate = float(amount) / float(amount_currency or amount)

        # devolvemos el rate <:o)
        return currency_rate

    @staticmethod
    def get_invoice_type(invoice):
        type_a = invoice.env.ref("l10n_ar_afip_tables.account_denomination_a")
        type_b = invoice.env.ref("l10n_ar_afip_tables.account_denomination_b")
        type_c = invoice.env.ref("l10n_ar_afip_tables.account_denomination_c")
        type_d = invoice.env.ref("l10n_ar_afip_tables.account_denomination_d")
        type_e = invoice.env.ref("l10n_ar_afip_tables.account_denomination_e")
        type_m = invoice.env.ref("l10n_ar_afip_tables.account_denomination_m")
        type_i = invoice.env.ref("l10n_ar_afip_tables.account_denomination_i")

        if invoice.is_debit_note:
            types = {
                type_a: "002",
                type_b: "007",
                type_c: "012",
                type_e: "020",
                type_m: "052",
            }
            return types.get(invoice.denomination_id) or ""
        else:
            if invoice.type in ["out_invoice", "in_invoice"]:
                types = {
                    type_a: "001",
                    type_b: "006",
                    type_c: "011",
                    type_d: "066",
                    type_e: "019",
                    type_m: "051",
                    type_i: "099",
                }
                return types.get(invoice.denomination_id) or ""
            elif invoice.type in ["out_refund", "in_refund"]:
                types = {
                    type_a: "003",
                    type_b: "008",
                    type_c: "013",
                    type_e: "021",
                    type_m: "053",
                }
                return types.get(invoice.denomination_id) or ""
            else:
                return ""

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

    @staticmethod
    def get_company_currency(invoice):
        return invoice.company_id.currency_id

    @staticmethod
    def get_invoice_currency(invoice):
        return invoice.currency_id

    @staticmethod
    def are_company_and_invoice_same_currency(invoice):
        company_currency_id = PresentationTools.get_company_currency(invoice).id
        invoice_currency_id = PresentationTools.get_invoice_currency(invoice).id
        return company_currency_id == invoice_currency_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
