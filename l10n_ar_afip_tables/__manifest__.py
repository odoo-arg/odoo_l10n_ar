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

    'name': 'l10n_ar_afip_tables',

    'version': '1.0',

    'summary': 'Datas of tables of afip V.0 25082010-5',

    'description': """ Datas of tables of afip V.0 25082010-5,
mapped with models using l10n_ar_codes application
""",

    'author': 'OPENPYME S.R.L.',

    'website': 'http://www.openpyme.com.ar',

    'category': 'base',

    'depends': [
        'l10n_ar',
    ],

    'data': [
        'views/afip_tables_configuration.xml',
        'views/account_denomination_view.xml',
        'data/res_country_state.xml',
        'data/res_currency.xml',
        'data/account_denomination.xml',
        'data/afip_voucher_type.xml',
        'data/partner_document_type.xml',
        'data/account_tax.xml',
        'data/account_fiscal_position.xml',
        'data/afip_concept.xml',
        'security/ir.model.access.csv',
        'data/security.xml',
    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: