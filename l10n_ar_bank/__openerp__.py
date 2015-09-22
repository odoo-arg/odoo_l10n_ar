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
    'active': False,

    'author': 'OpenERP - Team de Localizacion Argentina',

    'category': 'Localization',

    'depends': [

        'base',
        'l10n_ar_states'

    ],

    'summary': 'Banks of Argentina',

    'external_dependencies': {

        'python': [

            'BeautifulSoup',
            'geopy',
        ],

    },

    'installable': True,

    'license': 'AGPL-3',

    'name': 'Banks',

    'test': ['test/l10n_ar_banks_wizard.yml'],

    'data': [

        'data/res_bank.xml',
        'l10n_ar_bank.xml',
        'l10n_ar_bank_menu.xml',
        'wizard/wiz_l10n_ar_bank.xml',

    ],

    'version': '2.7.231',

    'website': 'https://launchpad.net/~openerp-l10n-ar-localization'

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
