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

    'name': 'Currency inverse rate',

    'version': '1.0',

    'category': 'base',

    'summary': 'Posibilidad de cargar la tasa de la moneda inversamente',

    'author': 'OPENPYME S.R.L',

    'website': '',

    'depends': [
        'base'
    ],

    'data': [
        'views/res_currency_view.xml',
        'views/res_currency_rate_view.xml'
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': """ Posibilidad de cargar la tasa de la moneda inversamente """,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
