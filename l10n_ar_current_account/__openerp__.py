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

    'name': 'Current account',

    'version': '1.0',

    'summary': 'Current account and conciliations of documents',

    'author': 'OPENPYME SRL',

    'website': 'openpyme.com.ar',

    'category': 'Generic Modules/Accounting',

    'depends': [

        'account',
        'l10n_ar_point_of_sale',
        'account_voucher',
        'sale_stock',
    ],

    'data': [

        'views/res_partner_view.xml',
        'views/current_account_view.xml',
        'views/res_partner_document_imputation_view.xml',
        'wizard/current_account_imputation_wizard_view.xml',
        'data/current_account_data.xml'

    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
