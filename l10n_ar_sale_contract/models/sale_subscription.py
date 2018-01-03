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


class SaleSubscription(models.Model):

    _inherit = 'sale.subscription'

    @api.returns('account.invoice')
    def _recurring_create_invoice(self, automatic=False):
        account_invoice_proxy = self.env['account.invoice']
        invoices = super(SaleSubscription, self)._recurring_create_invoice(automatic=automatic)
        for invoice in account_invoice_proxy.browse(invoices):
            invoice.onchange_partner_id()
        return invoices

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: