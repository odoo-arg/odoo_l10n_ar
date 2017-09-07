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


class AccountInvoicePresentation(models.Model):
    _inherit = 'account.invoice.presentation'

    def generate_fiscal_credit_service_import_file(self):
        "Se genera el archivo de credito fiscal de servicios"
        fiscal_credit_file = presentation_builder.Presentation("ventasCompras", "creditoFiscalImportacionServ")

        return fiscal_credit_file

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

