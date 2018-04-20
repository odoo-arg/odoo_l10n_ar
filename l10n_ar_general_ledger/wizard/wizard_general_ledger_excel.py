# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
import StringIO
import base64
from collections import defaultdict
from datetime import datetime

import xlwt as xlwt
from openerp import models, fields, http, api
from openerp.addons.web.controllers.main import serialize_exception, content_disposition
from openerp.exceptions import ValidationError

COLS = {
    'fecha': 0,
    'cod_cuenta': 1,
    'nom_cuenta': 2,
    'debe': 3,
    'haber': 4,
    'ref': 5,
    'partner': 6,
}


class WizardGeneralLedgerExcel(models.TransientModel):
    _name = 'wizard.general.ledger.excel'

    date_from = fields.Date(
        string="Desde",
        default=fields.Date.today(),
        required=True,
    )

    date_to = fields.Date(
        string="Hasta",
        default=fields.Date.today(),
        required=True,
    )

    ledger = fields.Binary(
        string="Mayor"
    )

    @api.constrains('date_from', 'date_to')
    def check_dates(self):
        if self.date_from > self.date_to:
            raise ValidationError("La fecha desde no puede ser mayor a la fecha hasta.")

    def get_values(self, moves):
        """
        Genera una lista con datos (fecha, codigo de cuenta, nombre de cuenta, debe, haber, nombre de asiento y
        nombre de partner) de cada linea de asiento y se la asigna al asiento en un diccionario
        :param moves: recordset de asientos sobre los cuales se generaran los datos
        :return: diccionario con lineas por cada asiento
        """
        lines_by_move = defaultdict(list)
        for line in moves.mapped('line_ids').sorted(lambda l: (l.move_id.date, l.move_id.id)):
            account = line.account_id
            lines_by_move[line.move_id.name].append((datetime.strptime(line.date, '%Y-%m-%d').strftime('%d/%m/%Y'),
                                                     account.code.replace('.', ''), account.name, line.debit or '-',
                                                     line.credit or '-', line.name or '',
                                                     line.partner_id.name if line.partner_id else ''))
        return lines_by_move

    def fill_sheet(self, sheet, values):
        """
        Rellena una hoja de calculo con los valores suministrados (con formato similar al devuelto por get_values)
        :param sheet: la hoja a rellenar
        :param values: diccionario de valores (la key es un asiento y el value, una lista de tuplas)
        """
        style_regular = xlwt.easyxf('align: horiz left;')
        style_title = xlwt.easyxf('align: horiz left; font: bold on;')
        current_row = 0
        sheet.write(current_row, 0, "ASIENTO", style_title)
        sheet.write(current_row, 1, "FECHA", style_title)
        sheet.write(current_row, 2, "COD. CUENTA", style_title)
        sheet.write(current_row, 3, "CUENTA", style_title)
        sheet.write(current_row, 5, "DEBE", style_title)
        sheet.write(current_row, 7, "HABER", style_title)
        sheet.write(current_row, 8, "APUNTE", style_title)
        sheet.write(current_row, 9, "PARTNER", style_title)
        current_row += 1
        symbol = self.env.user.company_id.currency_id.symbol
        for move, lines in values.iteritems():
            for line in lines:
                sheet.write(current_row, 1, line[COLS.get('fecha')], style_regular)
                sheet.write(current_row, 2, line[COLS.get('cod_cuenta')], style_regular)
                sheet.write(current_row, 3, line[COLS.get('nom_cuenta')], style_regular)
                sheet.write(current_row, 4, symbol, style_regular)
                sheet.write(current_row, 5, line[COLS.get('debe')], style_regular)
                sheet.write(current_row, 6, symbol, style_regular)
                sheet.write(current_row, 7, line[COLS.get('haber')], style_regular)
                sheet.write(current_row, 8, line[COLS.get('ref')], style_regular)
                sheet.write(current_row, 9, line[COLS.get('partner')], style_regular)
                current_row += 1

            for x in [5, 7]:
                column_start = xlwt.Utils.rowcol_to_cell(current_row - len(lines), x)
                column_end = xlwt.Utils.rowcol_to_cell(current_row - 1, x)
                sheet.write(current_row, x-1, symbol, style_title)
                sheet.write(current_row, x, xlwt.Formula('SUM(' + column_start + ':' + column_end + ')'), style_title)
            sheet.write(current_row, 0, move, style_title)
            current_row += 1

    def generate_ledger(self):
        """
        Genera y descarga el libro mayor en formato xls
        :return: la descarga del archivo
        """
        moves = self.env['account.move'].search([('date', '>=', self.date_from), ('date', '<=', self.date_to)])
        values = self.get_values(moves)
        wb = xlwt.Workbook()
        sheet = wb.add_sheet("Mayor")
        self.fill_sheet(sheet, values)

        file_data = StringIO.StringIO()
        wb.save(file_data)
        file = base64.encodestring(file_data.getvalue())
        self.ledger = file

        date_from = fields.Date.from_string(self.date_from).strftime('%d-%m-%Y')
        date_to = fields.Date.from_string(self.date_to).strftime('%d-%m-%Y')
        filename = 'Libro mayor ' + date_from + ' - ' + date_to

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/download_general_ledger?wizard_id=%s&filename=%s' % (self.id, filename + '.xls'),
            'target': 'new',
        }


class WizardGeneralLedgerExcelRoute(http.Controller):
    @http.route('/web/binary/download_general_ledger', type='http', auth="public")
    @serialize_exception
    def download_general_ledger(self, debug=1, wizard_id=0, filename=''):  # pragma: no cover
        """ Descarga un documento cuando se accede a la url especificada en http route.
        :param debug: Si esta o no en modo debug.
        :param int wizard_id: Id del modelo que contiene el documento.
        :param filename: Nombre del archivo.
        :returns: :class:`werkzeug.wrappers.Response`, descarga del archivo excel.
        """
        file = base64.b64decode(http.request.env['wizard.general.ledger.excel'].browse(int(wizard_id)).ledger or '')
        return http.request.make_response(file, [('Content-Type', 'application/excel'),
                                                 ('Content-Disposition', content_disposition(filename))])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
