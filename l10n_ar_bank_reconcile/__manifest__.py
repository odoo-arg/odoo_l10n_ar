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

{

    'name': 'Bank reconcile',

    'version': '1.0',

    'category': '',

    'summary': 'Bank reconcile',

    'author': 'OPENPYME S.R.L',

    'website': 'openpyme.com.ar',

    'depends': [

        'l10n_ar',

    ],

    'data': [
    
        'views/account_bank_reconcile.xml',
        'views/account_bank_reconcile_line.xml',
        'views/account_move_line.xml',
        'views/account_reconcile_remove_line.xml',
        'wizard/views/bank_reconcile_wizard.xml',
        'security/ir.model.access.csv',

    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': """
Bank reconcile
======================================
* .
""",

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
