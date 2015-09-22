# -*- coding: utf-8 -*-
##############################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{

    'name': 'States',

    'category': 'Localization',

    'author': 'OpenERP - Team de Localizacion Argentina',

    'depends': [

        'base',

    ],

    'summary': 'States for Argentina',

    'license': 'AGPL-3',

    'test': [

        'tests/test.yml',

    ],

    'data': [

        'data/res_country_state.xml',
        # Esta cargado el data completo con CUIT de paises pero no realiza la actualizacion.
        #'data/res_country.xml',
        'views/res_country_view.xml',
        'views/res_country_state_view.xml',

    ],

    'version': '1.0',

    'website': 'https://launchpad.net/~openerp-l10n-ar-localization',

    'active': False,

    'installable': True,


}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
