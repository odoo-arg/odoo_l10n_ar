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

    'name': 'Account invoice presentation',

    'version': '1.0',

    'category': 'Account',

    'summary': 'Presentacion ventas/compras',

    'author': 'OPENPYME S.R.L',

    'website': 'http://www.openpyme.com.ar',

    'depends': [
        'base_vat_ar',
        'account',
    ],

    'data': [
        'views/account_invoice_presentation.xml',
        'views/res_partner.xml',
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': 'Presentacion ventas/compras',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
