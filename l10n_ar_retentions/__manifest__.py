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

    'name': 'l10n_ar_retentions',

    'version': '1.0',

    'category': 'Accounting',

    'summary': 'Retenciones para Argentina',

    'author': 'OPENPYME S.R.L',

    'website': 'http://www.openpyme.com.ar',

    'depends': [
        'l10n_ar_account_payment',
        'l10n_ar_taxes',
    ],

    'data': [
        'views/retention_retention_view.xml',
        'views/account_payment_view.xml',
        'views/retention_activity_view.xml',
        'wizard/account_register_payments_wizard.xml',
        'data/retention_data.xml',
        'data/retention_activities.xml',
        'data/sequence.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': 'Contempla retenciones en la carga de pagos',

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
