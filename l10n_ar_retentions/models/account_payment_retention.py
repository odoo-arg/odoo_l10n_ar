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


class AccountPaymentRetention(models.Model):
    """
    Retenciones cargadas en pagos. Tener en cuenta que hay datos necesarios que se deberian desde
    el pago: Cuit, Moneda, Fecha, Tipo (Proveedor/Cliente)
    """

    _inherit = 'account.document.tax'
    _name = 'account.payment.retention'

    payment_id = fields.Many2one('account.payment', 'Pago', required=True, ondelete="cascade")
    currency_id = fields.Many2one(related='payment_id.currency_id', readonly=True)
    retention_id = fields.Many2one(
        'retention.retention',
        'Retencion',
        ondelete='restrict',
        required=True
    )
    certificate_no = fields.Char(string='Numero de certificado')
    activity_id = fields.Many2one(
        'retention.activity',
        'Actividad',
    )

    @api.onchange('retention_id')
    def onchange_retention_id(self):
        if self.retention_id:
            self.update({
                'name': self.retention_id.name,
                'jurisdiction': self.retention_id.jurisdiction,
            })
        else:
            self.update({
                'name': None,
                'jurisdiction': None,
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
