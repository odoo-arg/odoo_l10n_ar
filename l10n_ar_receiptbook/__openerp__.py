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

    "name": "Receiptbooks",

    "version": "1.0",

    "depends": [

        "account_voucher",
        "account"

    ],

    "author" : "OPENPYME SRL",

    "website": "openpyme.com.ar",

    "category": "Accounting & Finance",

    "summary": "Provides receipt book for vouchers",

    'data': [

        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/receiptbook_view.xml',
        'views/account_voucher_view.xml',
        'workflow/account_voucher_workflow.xml',
        'data/receiptbook_data.xml',

    ],

    'installable': True,

    'active': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
