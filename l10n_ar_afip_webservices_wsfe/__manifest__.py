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

    'name': 'AFIP: Web service de factura electrónica',

    'version': '1.0',

    'category': 'Localization',

    'summary': 'AFIP: Factura electrónica',

    'author': 'OPENPYME S.R.L',

    'website': 'http://www.openpyme.com.ar',

    'depends': [
        'l10n_ar_afip_webservices_wsaa',
        'l10n_ar_perceptions'
    ],

    'data': [
        'views/wsfe_configuration_view.xml',
        'views/account_invoice_view.xml',
        'views/wsfe_request_detail_view.xml',
        'data/document_book_type.xml',
        'security/ir.model.access.csv'
    ],

    'installable': True,

    'auto_install': False,

    'application': True,

    'description': """
AFIP: Webservices de factura electrónica
==================================
    Factura electrónica.\n
    Configuración de puntos de venta para factura electrónica.
    """,

}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
