# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api
from lxml import etree

PAYMENT_TYPE = {
    'inbound': 'sale',
    'outbound': 'purchase'
}


class AccountAbstractPayment(models.AbstractModel):

    _inherit = 'account.abstract.payment'

    retention_ids = fields.One2many(
        'account.payment.retention',
        'payment_id',
        'Retenciones'
    )

    @api.onchange('retention_ids')
    def onchange_retention_ids(self):
        self.recalculate_amount()

    def set_payment_methods_vals(self):

        vals = super(AccountAbstractPayment, self).set_payment_methods_vals()

        retentions = [
            {'amount': retention.amount, 'account_id': retention.retention_id.tax_id.account_id.id}
            for retention in self.retention_ids
        ]

        return vals+retentions

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Le setiamos el dominio a las retenciones segun desde donde se abre la vista de pagos """

        res = super(AccountAbstractPayment, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                                  toolbar=toolbar, submenu=submenu)

        # Buscamos si el campo de retention_ids existe en la vista y si tiene una vista tree
        if res['fields'].get('retention_ids') and res['fields'].get('retention_ids').get('views').get('tree'):
            arch = res['fields']['retention_ids']['views']['tree']['arch']
            doc = etree.XML(arch)

            # Buscamos el campo retention_id dentro del tree nuevo y le agregamos el dominio segun el tipo de pago
            for node in doc.xpath("//field[@name='retention_id']"):

                payment_type = self.env.context.get('default_payment_type')
                if not payment_type:

                    # Para el caso que el pago se haga desde la factura
                    invoice_type = self.env.context.get('type')
                    if invoice_type:
                        payment_type = 'outbound' if invoice_type == 'in_invoice' else 'inbound'

                    # Para el caso que sea desde el wizard de pagos
                    else:
                        if self.env.context.get('active_model') == 'account.invoice':
                            invoice = self.env['account.invoice'].browse(self.env.context.get('active_id'))
                            if invoice:
                                payment_type = 'outbound' if invoice.type in ['in_invoice', 'out_refund'] else 'inbound'

                if payment_type:
                    node.set('domain', "[('type_tax_use', '=','"+PAYMENT_TYPE.get(payment_type)+"')]")
                    res['fields']['retention_ids']['views']['tree']['arch'] = etree.tostring(doc)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
