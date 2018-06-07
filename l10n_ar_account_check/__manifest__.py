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

    'name': 'l10n_ar_account_check',

    'version': '1.0',

    'summary': 'Cheques propios y de terceros',

    'description': """
Cheques
==================================
    Cheques propios desde pagos.\n
    Cheques de terceros para cobros y pagos.\n
    Cobro de cheques propios.
    """,

    'author': 'OPENPYME S.R.L.',

    'website': 'http://www.openpyme.com.ar',

    'category': 'Accounting',

    'depends': [
        'l10n_ar_account_payment',
    ],

    'data': [
        'wizard/account_check_collect_wizard.xml',
        'security/treasury_security.xml',
        'security/ir.model.access.csv',
        'views/account_check_view.xml',
        'views/res_company_view.xml',
        'views/account_payment_view.xml',
        'views/account_checkbook_view.xml',
        'views/menu.xml',
        'wizard/account_register_payments_view.xml',
        'data/res_company.xml',
        'data/security.xml',
    ],

    'active': False,

    'installable': True,

}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: