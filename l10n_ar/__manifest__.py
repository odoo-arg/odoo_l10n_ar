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

    'name': 'l10n_ar',

    'version': '1.0',

    'summary': 'Datas of taxes and accounts',

    'description': """ Datas of a custom chart of account and taxes """,

    'author': 'OPENPYME S.R.L.',

    'website': 'http://www.openpyme.com.ar',

    'category': 'Accounting',

    'depends': [
        'base_vat_ar',
        'account',
        'base_codes'
    ],

    'data': [
        'data/company_data.xml',
        'data/account_type_data.xml',
        'data/account_chart_template_data.xml',
        'data/account_chart_data.xml',
        'data/account_tax_data.xml',
        'data/account_chart_template_data.yml',
        'data/bank_update.xml',
        'views/account_tax_view.xml',
        'views/res_bank.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'wizard/views/update_banks_wizard.xml'
        
    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: