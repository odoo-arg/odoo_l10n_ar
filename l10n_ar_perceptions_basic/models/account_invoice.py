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

from openerp import models, fields, api
from openerp.exceptions import Warning


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    perception_ids = fields.One2many(
        'perception.tax.line',
        'invoice_id',
        string='Percepcion',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    #~ SE COMENTA PARTE DE ESTA FUNCION PARA NO ESCRIBIR LA MOVE LINE CON EL IMPORTE BASE DE LA PERCEPCION
    @api.multi
    def finalize_invoice_move_lines(self, move_lines):

        for p in self.perception_ids:

            #~ ESCRIBIMOS LA FECHA DE LA FACTURA EN LA PERCEPCIONES PARA AQUELLAS
            #~ QUE NO TENIAN UNA FECHA.
            if not p.date:

                p.date = self.date_invoice or time.strftime('%Y-%m-%d')

        return move_lines


    #~ SE AGREGA A LA ACCION DE REFUND LAS LINEAS DE PERCEPCION
    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        """ Prepare the dict of values to create the new refund from the invoice.
            This method may be overridden to implement custom
            refund generation (making sure to call super() to establish
            a clean extension chain).

            :param record invoice: invoice to refund
            :param string date: refund creation date from the wizard
            :param integer period_id: force account.period from the wizard
            :param string description: description of the refund from the wizard
            :param integer journal_id: account.journal from the wizard
            :return: dict of value to create() the refund
        """

        values = super(AccountInvoice, self)._prepare_refund(invoice, date=None, period_id=None, description=None, journal_id=None)

        values['perception_ids'] = self._refund_cleanup_lines(invoice.perception_ids)

        return values


AccountInvoice()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
