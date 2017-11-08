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

    "name": "Retentions Advance",

    "summary": """Retenciones""",

    "description": """Retenciones""",

    "author": "OPENPYME SRL",

    "website": "www.openpyme.com.ar",

    "category": "Account",

    "version": "1.0",

    "depends": [

        "l10n_ar_retentions",
        # "l10n_ar_receiptbook",
        # "l10n_ar_point_of_sale",
        # "l10n_ar_invoice_analysis"

    ],

    "data": [

        'security/ir.model.access.csv',
        # 'wizard/compute_retention_wizard_view.xml',
        # 'wizard/compute_retention_invoice_view.xml',
        'views/retention_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/retention_activity_view.xml',
        'data/retention_activities.xml',

    ],

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
