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

from openerp import models, fields, api, _

class res_partner(models.Model):

    _inherit = "res.partner"

    @api.one
    def get_imputations_quantity(self):

        self.count_imputations = self.env['res.partner.imputation'].search_count([('partner_id', '=', self.id),('state', '=', 'valid')])

    count_imputations = fields.Integer('Imputaciones', compute='get_imputations_quantity')

    @api.multi
    def get_partner_imputation_documents(self):

        return {

            'name': _('Documentos imputados'),
            'views': [[False, "tree"], [False,"form"]],
            'domain': [('partner_id', '=', self.id)],
            'res_model': 'res.partner.imputation',
            'type': 'ir.actions.act_window',
        }

    #TODO: Unificar la funcion con la de _get_customer_move_lines / cuentas
    def _get_supplier_move_lines(self, customer_move_lines=[], supplier_move_lines=[]):

        current_account_proxy = self.env['current.account']        
        current_account_type = 'supplier'
        
        for move_line in supplier_move_lines:

            multiplier = 1 if move_line.credit > 0 else -1
            voucher = self._check_for_voucher(move_line)
            doc_type = 'op' if voucher else 'otro'
            total = move_line.credit if move_line.credit > 0 else -move_line.debit
            residual = move_line.amount_residual * multiplier
            subtotal = total
            denomination = None
            name = move_line.ref
            date = move_line.date
            state = 'conciled' if (move_line.reconcile_id or (move_line.reconcile_partial_id and move_line.amount_residual < 0))  else 'open'
            invoice_id = None
            voucher_id = None

            if move_line.invoice:


                currency_rate = abs( total / move_line.amount_currency) if move_line.amount_currency else 1

                doc_type = self._check_invoice_type(move_line)
                residual = move_line.invoice.residual * currency_rate * multiplier
                subtotal = move_line.invoice.amount_untaxed * currency_rate * multiplier
                denomination = move_line.invoice.denomination_id.name
                name = move_line.invoice.internal_number
                invoice_id = move_line.invoice.id

            if voucher:

                voucher_id = voucher.id

            current_account_proxy.create({
                'partner_id': self.id,
                'doc_type': doc_type,
                'denomination': denomination,
                'name': name,
                'date': date,
                'residual': residual,
                'subtotal': subtotal,
                'total': total,
                'state': state,
                'invoice_id': invoice_id,
                'voucher_id': voucher_id,
                'move_line_id': move_line.id,
                'current_account_type': current_account_type,
            })            
    
        for move_line in customer_move_lines:

            multiplier = 1 if move_line.credit > 0 else -1
            voucher = self._check_for_voucher(move_line)
            doc_type = 'rec' if voucher else 'otro'
            total = move_line.credit if move_line.credit > 0 else -move_line.debit
            residual = move_line.amount_residual * multiplier
            subtotal = total
            denomination = None
            name = move_line.ref
            date = move_line.date
            state = 'conciled' if (move_line.reconcile_id or (move_line.reconcile_partial_id and move_line.amount_residual < 0))  else 'open'
            invoice_id = None
            voucher_id = None
            
            if move_line.invoice:

                doc_type = self._check_invoice_type(move_line)
                residual = move_line.invoice.residual * multiplier
                subtotal = move_line.invoice.amount_untaxed * multiplier
                denomination = move_line.invoice.denomination_id.name
                name = move_line.invoice.internal_number
                invoice_id = move_line.invoice.id

            if voucher:

                voucher_id = voucher.id

            current_account_proxy.create({
                'partner_id': self.id,
                'doc_type': doc_type,
                'denomination': denomination,
                'name': name,
                'date': date,
                'residual': residual,
                'subtotal': subtotal,
                'total': total,
                'state': state,
                'invoice_id': invoice_id,
                'voucher_id': voucher_id,
                'move_line_id': move_line.id,
                'current_account_type': current_account_type,
            })
       
    @api.multi
    def get_supplier_current_account(self):

        move_line_proxy = self.env['account.move.line']
        current_account_proxy = self.env['current.account']
        current_accounts = current_account_proxy.search([('partner_id', '=', self.id)])
        current_accounts.unlink()

        supplier_move_lines = move_line_proxy.search([
            ('state','=','valid'), 
            ('account_id.type', '=', 'payable'), 
            ('partner_id', '=', self.id)
        ])

        self._get_supplier_move_lines(supplier_move_lines=supplier_move_lines)

        cusomer_move_lines = move_line_proxy.search([
            ('state','=','valid'), 
            ('account_id.type', '=', 'receivable'), 
            ('partner_id', '=', self.id)
        ])

        self._get_supplier_move_lines(cusomer_move_lines)
        
        return {

            'name': _('Current Account'),
            'views': [[False, "tree"]],
            'domain': [('partner_id', '=', self.id)],
            'context': {'search_default_state': 'open'},
            'res_model': 'current.account',
            'type': 'ir.actions.act_window',
        }

     
        
    #TODO: Unificar la funcion con la de _get_supplier_move_lines / cuentas
    def _get_customer_move_lines(self, customer_move_lines=[], supplier_move_lines=[]):

        current_account_proxy = self.env['current.account']        
        current_account_type = 'customer'

        for move_line in customer_move_lines:

            multiplier = 1 if move_line.debit > 0 else -1
            voucher = self._check_for_voucher(move_line)
            doc_type = 'rec' if voucher else 'otro'
            total = move_line.debit if move_line.debit > 0 else -move_line.credit
            residual = move_line.amount_residual * multiplier
            subtotal = total
            denomination = None
            name = move_line.ref
            date = move_line.date
            state = 'conciled' if (move_line.reconcile_id or (move_line.reconcile_partial_id and move_line.amount_residual < 0))  else 'open'
            invoice_id = None
            voucher_id = None

            if move_line.invoice:

                doc_type = self._check_invoice_type(move_line)
                residual = move_line.invoice.residual * multiplier
                subtotal = move_line.invoice.amount_untaxed * multiplier
                denomination = move_line.invoice.denomination_id.name
                name = move_line.invoice.internal_number
                invoice_id = move_line.invoice.id

            if voucher:

                voucher_id = voucher.id

            current_account_proxy.create({
                'partner_id': self.id,
                'doc_type': doc_type,
                'denomination': denomination,
                'name': name,
                'date': date,
                'residual': residual,
                'subtotal': subtotal,
                'total': total,
                'state': state,
                'invoice_id': invoice_id,
                'voucher_id': voucher_id,
                'move_line_id': move_line.id,
                'current_account_type': current_account_type
            })
   
        for move_line in supplier_move_lines:

            multiplier = 1 if move_line.debit > 0 else -1
            voucher = self._check_for_voucher(move_line)
            doc_type = 'op' if voucher else 'otro'
            total = move_line.debit if move_line.debit > 0 else -move_line.credit
            residual = move_line.amount_residual * multiplier
            subtotal = total
            denomination = None
            name = move_line.ref
            date = move_line.date
            state = 'conciled' if (move_line.reconcile_id or (move_line.reconcile_partial_id and move_line.amount_residual < 0))  else 'open'
            invoice_id = None
            voucher_id = None

            if move_line.invoice:

                currency_rate = abs( total / move_line.amount_currency) if move_line.amount_currency else 1

                doc_type = self._check_invoice_type(move_line)
                residual = move_line.invoice.residual * currency_rate * multiplier
                subtotal = move_line.invoice.amount_untaxed * currency_rate * multiplier
                denomination = move_line.invoice.denomination_id.name
                name = move_line.invoice.internal_number
                invoice_id = move_line.invoice.id

            if voucher:

                voucher_id = voucher.id

            current_account_proxy.create({
                'partner_id': self.id,
                'doc_type': doc_type,
                'denomination': denomination,
                'name': name,
                'date': date,
                'residual': residual,
                'subtotal': subtotal,
                'total': total,
                'state': state,
                'invoice_id': invoice_id,
                'voucher_id': voucher_id,
                'move_line_id': move_line.id,
                'current_account_type': current_account_type
            })
                                      
    @api.multi
    def get_customer_current_account(self):

        current_account_proxy = self.env['current.account']        
        move_line_proxy = self.env['account.move.line']
        current_accounts = current_account_proxy.search([('partner_id', '=', self.id)])
        current_accounts.unlink()
        cusomer_move_lines = move_line_proxy.search([
            ('state','=','valid'), 
            ('account_id.type', '=', 'receivable'), 
            ('partner_id', '=', self.id)
        ])
        
        self._get_customer_move_lines(cusomer_move_lines)

        supplier_move_lines = move_line_proxy.search([
            ('state','=','valid'), 
            ('account_id.type', '=', 'payable'), 
            ('partner_id', '=', self.id)
        ])

        self._get_customer_move_lines(supplier_move_lines=supplier_move_lines)
            
        return {

            'name': _('Current Account'),
            'views': [[False, "tree"]],
            'domain': [('partner_id', '=', self.id)],
            'context': {'search_default_state': 'open'},
            'res_model': 'current.account',
            'type': 'ir.actions.act_window',
        }

    def _check_invoice_type(self, move_line):

        invoice_type = None

        if move_line.invoice.type in ('in_invoice'):

            invoice_type = 'fcp'

            if move_line.invoice.is_debit_note:

                invoice_type = 'ndp'

        elif move_line.invoice.type in ('in_refund'):

            invoice_type = 'ncp'

        elif move_line.invoice.type in ('out_invoice'):

            invoice_type = 'fcc'

            if move_line.invoice.is_debit_note:

                invoice_type = 'ndc'

        elif move_line.invoice.type in ('out_refund'):

            invoice_type = 'ncc'

        return invoice_type

    def _check_for_voucher(self, move_line):

        voucher = self.env['account.voucher'].search(['&', '|', ('number', '=', move_line.name), ('reference', '=', move_line.ref),
        '&', ('state', '=', 'posted'), ('partner_id', '=', move_line.partner_id.id)])

        if voucher:

            voucher = voucher[0]

        return voucher

res_partner()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
