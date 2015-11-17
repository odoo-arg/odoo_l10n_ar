# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    All Rights Reserved. See AUTHORS for details.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
    "name": "Point of Sale",

    "version": "1.0",

    "author" : "OPENPYME SRL",

    "website": "openpyme.com.ar",

    "depends": [

        'base',
        'sale',
        'purchase',
        'account',
        'account_accountant',
        'base_vat_ar',
        'l10n_ar_chart_of_account',

    ],

    "license": "GPL-3",

    "category": "Localization",

    "summary": "Point of sale",

    "data": [

        'security/ir.model.access.csv',
        'security/security.xml',
        'data/partner_data.xml',
        'data/pos_ar_type.xml',
        'views/pos_ar_view.xml',
        'views/account_invoice_view.xml',
        'views/fiscal_position_view.xml',
        'views/account_view.xml',

    ],

    'installable': True,

    'active': False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
