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

    "name": "Retentions",

    "summary": """Retenciones""",

    "description": """Retenciones""",

    "author": "OPENPYME SRL",

    "website": "www.openpyme.com.ar",

    'category': 'Account',

    'depends': [

        'base',
        'account',
        'account_accountant',
        'account_voucher',
        'l10n_ar_chart_of_account',
        'l10n_ar_account_payment',
        'l10n_ar_account_check',

    ],

    'data': [

        'data/retention_data.xml',
        'data/security.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
        'views/retention_retention.xml',
        'views/retention_tax_line.xml',
        'views/voucher_payment_receipt_view.xml',

    ],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
