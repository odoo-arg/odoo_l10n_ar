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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api
from openerp.exceptions import ValidationError


class ReportElectronicInvoice(models.AbstractModel):

    _name = 'report.l10n_ar_electronic_invoice_report.report_electronic_invoice'
    _table = 'report_electronic_invoice'

    @api.model
    def render_html(self, docids, data=None):

        report_obj = self.env['report']
        docs = self.env['account.invoice'].browse(docids)
        for doc in docs:
            self._validate_electronic_invoice_fields(doc)

        docargs = {
            'doc_ids': docids,
            'doc_model': self.env['account.invoice'],
            'docs': docs,
        }
        return report_obj.render('l10n_ar_electronic_invoice_report.report_electronic_invoice', docargs)

    @staticmethod
    def _validate_electronic_invoice_fields(doc):
        """
        Valida que esten los campos necesarios para la impresión del reporte de factura electronica
        :param doc: Model account.invoice, documento a validar sus campos
        """
        company = doc.company_id
        if not (company.start_date and company.iibb_number and company.street and company.city):
            raise ValidationError("Antes de imprimir, configurar la fecha de inicio de actividades"
                                  ", numero de IIBB y direccion de la empresa")

        if not doc.cae:
            raise ValidationError("No se puede imprimir un documento sin CAE")

        if doc.state not in ['open', 'paid']:
            raise ValidationError("No se puede imprimir un documento en estado borrador o cancelado")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
