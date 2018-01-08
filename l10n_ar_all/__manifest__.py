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

    'name': 'l10n_ar_all',

    'version': '1.0',

    'summary': 'Localizacion Argentina',

    'description': """
Modulo encargado de instalar todos los modulos requeridos para la localizacion Argentina.
    """,

    'author': 'OPENPYME S.R.L.',

    'website': 'http://www.openpyme.com.ar',

    'category': 'Localization',

    'depends': [
        'l10n_ar_reject_checks',
        'l10n_ar_account_check_sale',
        'l10n_ar_account_payment_report',
        'l10n_ar_electronic_invoice_report',
        'l10n_ar_bank_reconcile',
        'l10n_ar_invoice_presentation',
        'l10n_ar_retentions_sifere',
        'l10n_ar_perceptions_sifere',
        'l10n_ar_payment_imputation',
    ],

    'data': [

    ],

    'active': False,

    'installable': True,

}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: