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

    "name": "Taxes report in xls",

    "version": "1.0",

    "depends": [

        "base",
        "account",
        "account_accountant",
        "sale",
        "purchase",
    ],

    "author": "OPENPYME SRL",

    "category": "Taxes Reports",

    "description":

        """Export in xls of the taxes based on tax configuration.""",

    "data": [

        'security/ir.model.access.csv',
        'view/taxes_report_view.xml',

    ],

    "installable": True,

    "auto_install": False,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
