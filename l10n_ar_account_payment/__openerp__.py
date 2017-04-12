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

    "name": "Account Payments Methods",

    "version": "1.0",

    "depends": ["base", "account_voucher", "account_accountant"],

    "author": "OPENPYME SRL",

    "website": "openpyme.com.ar",

    "license": "GPL-3",

    "category": "Accounting",

    "summmary": "Implementation of Receipt/Payments for Argentina",

    "data": [

        'security/ir.model.access.csv',
        'security/security.xml',
        'views/voucher_payment_receipt_view.xml',
        'views/payment_mode_receipt_view.xml',

    ],

    'installable': True,

    'active': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
