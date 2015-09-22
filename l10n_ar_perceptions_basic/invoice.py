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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
import time
from openerp import api
import logging
_logger = logging.getLogger(__name__)

class perception_tax_line(osv.osv):

    _name = "perception.tax.line"

    _description = "Perception Tax Line"

    _columns = {

        'name': fields.char('Perception', required=True, size=64),
        'date': fields.date('Date', select=True),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', ondelete='cascade'),
        'account_id': fields.many2one('account.account', 'Tax Account', required=True,
                                      domain=[('type','<>','view'),('type','<>','income'), ('type', '<>', 'closed')]),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'perception_id': fields.many2one('perception.perception', 'Perception Configuration', required=True, help="Perception configuration used '\
                                       'for this perception tax, where all the configuration resides. Accounts, Tax Codes, etc."),
        'base_code_id': fields.many2one('account.tax.code', 'Base Code', help="The account basis of the tax declaration."),
        'base_amount': fields.float('Base Code Amount', digits_compute=dp.get_precision('Account')),
        'tax_code_id': fields.many2one('account.tax.code', 'Tax Code', help="The tax basis of the tax declaration."),
        'tax_amount': fields.float('Tax Code Amount', digits_compute=dp.get_precision('Account')),
        'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'partner_id': fields.related('invoice_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', readonly=True),
        'state_id': fields.many2one('res.country.state', string="State/Province"),
        'ait_id': fields.many2one('account.invoice.tax', 'Invoice Tax', ondelete='cascade'),
        'vat': fields.related('invoice_id', 'partner_id', 'vat', type='char', string='CIF/NIF', readonly=True),


    }

    def onchange_perception(self, cr, uid, ids, perception_id, context):
        if not perception_id:
            return {}
        perception_obj = self.pool.get('perception.perception')
        perception = perception_obj.browse(cr, uid, perception_id)
        vals = {}
        vals['name'] = perception.name
        vals['account_id'] = perception.tax_id.account_collected_id.id
        vals['base_code_id'] = perception.tax_id.base_code_id.id
        vals['tax_code_id'] = perception.tax_id.tax_code_id.id
        vals['state_id'] = perception.state_id.id
        return {'value': vals}

    @api.v8
    def _compute(self, perception_id, base, amount):
        # Buscamos la account_tax referida a esta perception_id

        perception = self.env['perception.perception'].browse(perception_id)
        tax = perception.tax_id
        base_amount = base * tax.base_sign
        tax_amount = amount * tax.ref_tax_sign

        return (tax_amount, base_amount)

perception_tax_line()


class account_invoice(osv.osv):


    _name = 'account.invoice'

    _inherit = 'account.invoice'

    _columns = {

        'perception_ids': fields.one2many('perception.tax.line', 'invoice_id', 'Perception', readonly=True, states={'draft':[('readonly', False)]}),

    }

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        """ finalize_invoice_move_lines(move_lines) -> move_lines

            Hook method to be overridden in additional modules to verify and
            possibly alter the move lines to be created by an invoice, for
            special cases.
            :param move_lines: list of dictionaries with the account.move.lines (as for create())
            :return: the (possibly updated) final move_lines to create for this invoice
        """

        # Como nos faltan los account.move.line de las bases imponibles de las percepciones
        # utilizamos este hook para agregarlos
        plt_obj = self.env['perception.tax.line']
        company_currency = self.company_id.currency_id.id
        current_currency = self.currency_id.id

        for p in self.perception_ids:
            sign = p.perception_id.tax_id.base_sign
            tax_amount, base_amount = plt_obj._compute(p.perception_id.id, p.base, p.amount)

            # ...y ahora creamos la linea contable perteneciente a la base imponible de la perception
            # Notar que credit & debit son 0.0 ambas. Lo que cuenta es el tax_code_id y el tax_amount
            move_line = {
                'name': p.name + '(Base Imp)',
                'ref': self.internal_number or False,
                'debit': 0.0,
                'credit': 0.0,
                'account_id': p.account_id.id,
                'tax_code_id': p.base_code_id.id,
                'tax_amount': base_amount,
                'journal_id': self.journal_id.id,
                'period_id': self.period_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * p.amount or 0.0,
                'date': self.date_invoice or time.strftime('%Y-%m-%d'),
                'date_maturity': self.date_due or False,
            }

            # Si no tenemos seteada la fecha, escribimos la misma que la de la factura
            if not p.date:
                p.write({'date': move_line['date']})

            move_lines.insert(len(move_lines)-1, (0, 0, move_line))
        return move_lines

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
