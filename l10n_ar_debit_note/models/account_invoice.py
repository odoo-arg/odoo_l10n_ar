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


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    is_debit_note = fields.Boolean('Es nota de debito?')

    def check_invoice_duplicity(self, additional_domains=None):
        if self.is_debit_note:
            additional_domains = [('is_debit_note', '=', True)]
        return super(AccountInvoice, self).check_invoice_duplicity(additional_domains)

    @api.multi
    def name_get(self):
        """ Utilizamos la idea original, pero cambiando los parametros """

        types = {
            'out_invoice': 'FCC',
            'in_invoice': 'FCP',
            'out_refund': 'NCC',
            'in_refund': 'NCP',
            'out_debit_note': 'NDC',
            'in_debit_note': 'NDP',
        }

        result = []

        for inv in self:
            if inv.is_debit_note:
                if inv.type == 'in_invoice':
                    invoice_type = types.get('in_debit_note')
                else:
                    invoice_type = types.get('out_debit_note')
            else:
                invoice_type = types.get(inv.type)

            # EJ FC A 0001-00000001
            result.append((inv.id, "%s %s %s" % (
                invoice_type or '',
                inv.denomination_id.name or '',
                inv.name or inv.number or ''))
            )

        return result

    def get_next_number(self, additional_domains=None):
        if self.is_debit_note:
            additional_domains = [('document_type_id.type', '=', 'debit_note')]
        return super(AccountInvoice, self).get_next_number(additional_domains)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
