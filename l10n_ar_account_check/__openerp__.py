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

    'name': 'Account Checks',

    'version': '1.1',

    'summary': 'Allows to manage checks',

    'author': 'OPENPYME SRL',

    'website': 'openpyme.com.ar',

    'category': 'Generic Modules/Accounting',

    'depends': [

        'account',
        'account_voucher',
        'l10n_ar_account_payment',

    ],

    'data': [

        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/view_check_deposit.xml',
        'views/account_check_view.xml',
        'views/account_voucher_view.xml',
        'workflow/account_third_check_workflow.xml',
        'wizard/view_check_reject.xml',
        'views/partner_view.xml',

    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
