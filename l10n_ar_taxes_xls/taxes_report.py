# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, _
import time
from datetime import date, datetime
from operator import attrgetter

class taxes_report_xls(models.Model):

    _name = 'taxes.report.xls'

    fiscal_year_id = fields.Many2one('account.fiscalyear', 'Fiscal year')
    period_id = fields.Many2one('account.period', 'Period', required=True)
    name = fields.Char('Name')
    filename = fields.Char('Name', readonly=True)
    data = fields.Binary('Data', filename="filename", readonly=True)
    based_on = fields.Selection([
                ('sales', 'Sales'),
                ('purchases', 'Purchases'),
    ], required=True)

    @api.one
    def generate_taxes_report(self):

        filename = None
        # Digits rounding used for xls
        rounding = 2

        if self.based_on == 'sales':

            invoices = self.env['account.invoice'].search([('period_id', '=', self.period_id.id),
                                                           ('type', 'in', ('out_invoice', 'out_refund')),
                                                           ('state', 'not in', ('draft', 'cancel'))
                                                           ])

            filename = 'ventas '

        elif self.based_on == 'purchases':

            invoices = self.env['account.invoice'].search([('period_id', '=', self.period_id.id),
                                                           ('type', 'in', ('in_invoice', 'in_refund')),
                                                           ('state', 'not in', ('draft', 'cancel'))
                                                           ])

            filename = 'compras '

        taxesIds = self._get_taxes(invoices)

        taxes = self.env['account.tax'].browse(taxesIds)

        import StringIO
        import base64
        try:
            import xlwt
        except:
            raise osv.except_osv('Warning !','Please download python xlwt module from\nhttp://pypi.python.org/packages/source/x/xlwt/xlwt-0.7.2.tar.gz\nand install it')

        wbk = xlwt.Workbook()
        style1 = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;''borders: left thin, right thin, top thin')
        s1=0

        """ADDING A WORKSHEET ALONG WITH NAME"""
        sheet1 = wbk.add_sheet('Iva Ventas')

        sheet1.col(0).width = 2500
        sheet1.col(1).width = 6000
        sheet1.col(2).width = 4000
        sheet1.col(3).width = 6000
        sheet1.col(4).width = 1500
        sheet1.col(5).width = 4000
        sheet1.col(6).width = 4000

        for x in range(7, 7+len(taxesIds)):

            sheet1.col(x).width = 3500

        sheet1.write(s1,0,"Fecha",style1)
        sheet1.write(s1,1,"Razon Social",style1)
        sheet1.write(s1,2,"Cuit",style1)
        sheet1.write(s1,3,"Condicion IVA",style1)
        sheet1.write(s1,4,"Tipo",style1)
        sheet1.write(s1,5,"Numero",style1)
        sheet1.write(s1,6,"Provincia",style1)

        counter = 7
        tax_dict = {}

        for x in range(7, 7+(len(taxesIds))):

            sheet1.write(s1, counter , taxes[x-7].name+' - Base',style1)
            tax_dict[taxes[x-7].name+' - Base'] = counter
            counter += 1
            sheet1.write(s1, counter , taxes[x-7].name+ ' - Cantidad',style1)
            tax_dict[taxes[x-7].name+' - Cantidad'] = counter
            counter += 1


        sheet1.write(s1,counter,"Total",style1)

        for invoice in sorted(invoices, key=attrgetter('date_invoice', 'type', 'internal_number')):

            currency_rate = self._get_invoice_currency_rate(invoice)

            invoice_type = self._get_invoice_type(invoice)
            s1 += 1

            sheet1.write(s1, 0, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%d/%m/%Y'))
            sheet1.write(s1, 1, invoice.partner_id.name)
            sheet1.write(s1, 2, invoice.partner_id.vat)
            sheet1.write(s1, 3, invoice.partner_id.property_account_position.name)
            sheet1.write(s1, 4, invoice_type)
            sheet1.write(s1, 5, invoice.internal_number)
            sheet1.write(s1, 6, invoice.partner_id.state_id.name)


            tax_mapped_ids = invoice.tax_line.mapped('tax_id')

            for tax in tax_mapped_ids:

                base = 0
                amount = 0

                filter_tax_lines = invoice.tax_line.filtered(lambda r: r.tax_id == tax)

                for line in filter_tax_lines:

                    base += line.base * currency_rate
                    amount += line.amount * currency_rate

                if invoice.type == 'out_refund' or invoice.type == 'in_refund':

                    sheet1.write(s1, tax_dict.get(tax.name+' - Base'), - round(base, rounding))
                    sheet1.write(s1, tax_dict.get(tax.name+' - Cantidad'), - round(amount, rounding))

                else:

                    sheet1.write(s1, tax_dict.get(tax.name+' - Base'), round(base, rounding))
                    sheet1.write(s1, tax_dict.get(tax.name+' - Cantidad'), round(amount, rounding))


            if invoice.type == 'out_refund' or invoice.type == 'in_refund':

                 sheet1.write(s1, counter, - round(invoice.amount_total * currency_rate, rounding))

            else:

                sheet1.write(s1, counter, round(invoice.amount_total * currency_rate, rounding))


        for x in range(7, counter+1):

            column_start = xlwt.Utils.rowcol_to_cell(1, x)
            column_end = xlwt.Utils.rowcol_to_cell(s1, x)
            sheet1.write(s1+1, x, xlwt.Formula('SUM('+column_start+':'+column_end+')'))

        """PARSING DATA AS STRING """
        file_data=StringIO.StringIO()
        o=wbk.save(file_data)
        """STRING ENCODE OF DATA IN WKSHEET"""
        out=base64.encodestring(file_data.getvalue())
        filename ='Subdiario de iva ' + filename + self.period_id.name

        return self.write({'filename': filename + '.xls', 'data': out})

    def _get_taxes(self, invoices):

        taxes = []

        for invoice in invoices:

            for tax in invoice.tax_line:

                if tax.tax_id.id not in taxes:

                    taxes.append(tax.tax_id.id)

        return taxes

    def _get_invoice_type(self, invoice):

        res = None
        denomination = invoice.denomination_id.name

        if invoice.type in ('out_refund', 'in_refund'):

            res = 'NC '

        elif invoice.type in ('out_invoice', 'in_invoice'):

            if invoice.is_debit_note:

                res = 'ND '

            else:

                res = 'FC '


        res = res + denomination

        return res

    def _get_invoice_currency_rate(self, invoice):

        rate = 1

        if invoice.move_id.line_id:
            move = invoice.move_id.line_id[0]
            if move.amount_currency != 0:
                rate = abs((move.credit + move.debit) / move.amount_currency)

        return rate

taxes_report_xls()
