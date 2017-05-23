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

    'name': 'AFIP: Web service de autenticacion',

    'version': '1.0',

    'category': 'Localization',

    'summary': 'Autenticacion, creacion de certificados y llaves para los ws de AFIP',

    'author': 'OPENPYME S.R.L',

    'website': 'http://www.openpyme.com.ar',

    'depends': [
        'l10n_ar_afip_tables'
    ],

    'data': [
        'views/wsaa_configuration_view.xml'
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': """
AFIP: WebServices de autenticacion
==================================
    Creacion y configuracion de certificados y keys.\n
    Creacion y configuracion de tokens de acceso (TRA).
    """,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
