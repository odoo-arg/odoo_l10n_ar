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

{

    'name': 'Reporte de Pagos',

    'version': '1.0',

    'description': 'Reporte de Pagos',

    'author': 'OPENPYME S.R.L.',

    'summary': 'Reporte de Pagos',

    'category': 'Accounting',

    'depends': [

        'l10n_ar_account_payment',
        'l10n_ar_account_check',
        'l10n_ar_retentions',
       ],

    'data': [

        'report/account_payment_report.xml',
        'report/report_account_payment.xml',
    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
