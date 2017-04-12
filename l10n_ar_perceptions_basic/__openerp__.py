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

    "name": "Perceptions",

    "summary": """Percepciones""",

    "description": """Percepciones""",

    "author": "OPENPYME SRL",

    "website": "www.openpyme.com.ar",

    "category": "Account",

    "version": "1.0",

    "depends": [

        "base",
        "account",
        "account_accountant",
        "l10n_ar_point_of_sale",
        "l10n_ar_chart_of_account",

    ],

    "data": [

        "data/security.xml",
        "data/perception_data.xml",
        "security/ir.model.access.csv",
        "views/account_invoice.xml",
        "views/perception_perception.xml",
        "views/perception_tax_line.xml",

    ],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
