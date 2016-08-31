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
from openerp.exceptions import Warning
from datetime import date

class current_account_imputation_wizard(models.TransientModel):

    _name= 'current.account.imputation.wizard'

    imputation_debit_lines = fields.One2many('current.account.imputation.wizard.debit.line',
    'imputation_id', 'Imputation debit lines')
    imputation_credit_lines = fields.One2many('current.account.imputation.wizard.credit.line',
    'imputation_id', 'Imputation credit lines')
    debit_residual = fields.Float('Remaining to concile', readonly=True)
    credit_residual = fields.Float('Total to concile', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    wizard_type = fields.Selection((('customer','Cliente'),('supplier','Proveedor')), 'Tipo de wizard')
    
    @api.multi
    def concile_documents(self):

        self._create_moves(self._create_imputation())
        
        if self.partner_id.customer and not self.partner_id.supplier:
        
            return self.partner_id.get_customer_current_account();

        elif self.partner_id.supplier and not self.partner_id.customer:
            
            return self.partner_id.get_supplier_current_account();  
                  
        else:
             
            return {
    
                'name': _('Partner'),
                'views': [[False,"form"]],
                'res_id': self.partner_id.id,
                'res_model': 'res.partner',
                'type': 'ir.actions.act_window',
            }

    def _create_imputation(self):

        res_partner_imputation_proxy = self.env['res.partner.imputation']
        search_name = res_partner_imputation_proxy.search([('partner_id', '=', self.partner_id.id)], limit=1, order='number desc')
        number = search_name.number + 1 if search_name else 1
        name = 'IMPUTACION ' + str(number).zfill(4)

        imputation = res_partner_imputation_proxy.create({
            'date': date.today(),
            'name': name,
            'partner_id': self.partner_id.id,
            'number': number,
            'state': 'valid',
        })

        return imputation

    @api.one
    def _create_moves(self, imputation):

        document_imputation_proxy = self.env['res.partner.document.imputation']
        current_account_type = self.wizard_type
        journal = self.env['account.journal'].search([('code', '=', 'IMP')])
        move_date = date.today()
        period = self.env['account.period'].find(move_date)
        date_formated = move_date.strftime('%d/%m/%Y')
        ref = 'Imputacion '+ self.partner_id.name + ' - '+ date_formated
        if not journal or len(journal) > 1:

            raise Warning('No se pudo generar el asiento debido a que no se encontro el diario de imputaciones')

        
        total_to_concile = 0
        for credit in self.imputation_credit_lines:
            
            total_to_concile += credit.amount_to_concile
            
        total_conciled = 0
        for debit in self.imputation_debit_lines:
            
            total_conciled += debit.amount_to_concile
            
        if total_to_concile != total_conciled:
         
            raise Warning('Todavia queda restante a imputar a los documentos')
        
        move_line_proxy = self.env['account.move.line']
        move_line_pool = self.pool.get('account.move.line')

        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'state': 'draft',
            'period_id': period.id,
            'date': move_date,
            'ref': ref,
            })

        for credit_line in self.imputation_credit_lines:
            
            for debit_line in self.imputation_debit_lines:
                
                debit_line_created = None
                credit_line_created = None
                
                if credit_line.amount_to_concile > 0:

                    name = 'IMP ' + credit_line.document + ' ' + credit_line.document_number + ' / ' +  debit_line.document + ' ' + debit_line.document_number
                    debit_line_move_line = debit_line.move_line_id
                    debit_line_document = debit_line.document
                    debit_line_doc_number = debit_line.document_number
                    amount = 0

                    if debit_line.amount_to_concile > 0 and debit_line.amount_to_concile <= credit_line.amount_to_concile:

                        amount = debit_line.amount_to_concile
                        credit_line.amount_to_concile -= amount
                        credit_line.residual -= amount
                        debit_line.amount_to_concile = 0
                        debit_line.unlink()

                    elif debit_line.amount_to_concile > 0 and debit_line.amount_to_concile > credit_line.amount_to_concile:

                        amount = credit_line.amount_to_concile
                        debit_line.amount_to_concile -= credit_line.amount_to_concile
                        debit_line.residual -= credit_line.amount_to_concile
                        credit_line.amount_to_concile = 0

                    document_imputation_proxy.create({
                        'name': credit_line.document + ' ' + credit_line.document_number,
                        'imputation_to': debit_line_document + ' ' + debit_line_doc_number,
                        'amount': amount,
                        'imputation_id': imputation.id,
                    })
                    
                    imputation.move_id = move.id
                    
                    if current_account_type == 'customer':
                        
                        credit_line_created = move_line_proxy.create({
                            'name': name,
                            'account_id': debit_line_move_line.account_id.id,
                            'move_id': move.id,
                            'journal_id': journal.id,
                            'period_id': period.id,
                            'date': move_date,
                            'debit': 0.0,
                            'credit': amount,
                            'ref': ref,
                            'state': 'valid',
                            'partner_id': self.partner_id.id,
                        })
    
                        debit_line_created = move_line_proxy.create({
                            'name': name,
                            'account_id': credit_line.move_line_id.account_id.id,
                            'move_id': move.id,
                            'journal_id': journal.id,
                            'period_id': period.id,
                            'date': move_date,
                            'debit': amount,
                            'credit': 0.0,
                            'ref': ref,
                            'state': 'valid',
                            'partner_id': self.partner_id.id,
                        })

                    elif current_account_type == 'supplier':
                        
                        credit_line_created = move_line_proxy.create({
                            'name': name,
                            'account_id': debit_line_move_line.account_id.id,
                            'move_id': move.id,
                            'journal_id': journal.id,
                            'period_id': period.id,
                            'date': move_date,
                            'debit': amount,
                            'credit': 0.0,
                            'ref': ref,
                            'state': 'valid',
                            'partner_id': self.partner_id.id,
                        })
    
                        debit_line_created = move_line_proxy.create({
                            'name': name,
                            'account_id': credit_line.move_line_id.account_id.id,
                            'move_id': move.id,
                            'journal_id': journal.id,
                            'period_id': period.id,
                            'date': move_date,
                            'debit': 0.0,
                            'credit': amount,
                            'ref': ref,
                            'state': 'valid',
                            'partner_id': self.partner_id.id,
                        })
                    
                    
                    if debit_line_created and credit_line_created:

                        move_line_pool.reconcile_partial(self.env.cr, self.env.uid, [credit_line_created.id, debit_line_move_line.id], writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False)
                        move_line_pool.reconcile_partial(self.env.cr, self.env.uid, [debit_line_created.id, credit_line.move_line_id.id], writeoff_acc_id=False, writeoff_period_id=False, writeoff_journal_id=False)
                    
                    else:
                        
                        raise Warning('No se pudo realizar la imputacion')

    """" Onchange to recompute the credit residual

    :returns: New credit residual
    """
    @api.onchange('imputation_credit_lines')
    def onchange_imputation_credit_lines(self):

        credit_residual = 0
        debit_residual = 0

        for credit in self.imputation_credit_lines:

            credit_residual += credit.amount_to_concile
            debit_residual += credit.amount_to_concile

        for debit in self.imputation_debit_lines:

            debit.amount_to_concile = 0
            debit_residual -= debit.amount_to_concile

        self.credit_residual = credit_residual
        self.debit_residual = debit_residual

    """" Onchange to recompute the debit residual

    :returns: New debit residual
    """
    @api.onchange('imputation_debit_lines')
    def onchange_imputation_debit_lines(self):

        debit_residual = 0

        for credit in self.imputation_credit_lines:

            debit_residual += credit.amount_to_concile

        for debit in self.imputation_debit_lines:

            debit_residual -= debit.amount_to_concile

        self.debit_residual = debit_residual


current_account_imputation_wizard()

class current_account_imputation_wizard_debit_line(models.TransientModel):

    _name= 'current.account.imputation.wizard.debit.line'

    document = fields.Char('Document', readonly=True)
    document_number = fields.Char('Number', readonly=True)
    amount_total = fields.Float('Total', readonly=True)
    residual = fields.Float('Residual', readonly=True)
    amount_to_concile = fields.Float('Amount to concile')
    imputation_id = fields.Many2one('current.account.imputation.wizard', 'Imputation id')
    move_line_id = fields.Many2one('account.move.line', 'Linea del asiento')

    """ Constraints to the amounts

    :returns: Warning in case that the amount isnt right
    """
    @api.onchange('amount_to_concile')
    def onchange_amount_to_concile(self):

        if self.amount_to_concile > self.residual:

            self.amount_to_concile = 0

            return{

                'warning': {'title': _('User Error!'), 'message': _('You are trying to concile more than the residual of the document')}
            }

        if self.amount_to_concile < 0:

            self.amount_to_concile = 0

            return{

                'warning': {'title': _('User Error!'), 'message': _('Negative amounts are not allowed')}
            }

        self.imputation_id.onchange_imputation_debit_lines()
        if self.imputation_id.debit_residual < 0:

            self.amount_to_concile = 0

            return{

                'warning': {'title': _('User Error!'), 'message': _('You dont have that amount to concile')}
            }

current_account_imputation_wizard_debit_line()

class current_account_imputation_wizard_credit_line(models.TransientModel):

    _name= 'current.account.imputation.wizard.credit.line'

    document = fields.Char('Document', readonly=True)
    document_number = fields.Char('Number', readonly=True)
    amount_total = fields.Float('Total', readonly=True)
    residual = fields.Float('Residual', readonly=True)
    amount_to_concile = fields.Float('Amount to concile')
    imputation_id = fields.Many2one('current.account.imputation.wizard', 'Imputation id')
    move_line_id = fields.Many2one('account.move.line', 'Linea del asiento')

    """ Constraints to the amounts

    :returns: Warning in case that the amount isnt right
    """
    @api.onchange('amount_to_concile')
    def onchange_amount_to_concile(self):

        if self.amount_to_concile > self.residual:

            self.amount_to_concile = self.residual

            return{

                'warning': {'title': _('User Error!'), 'message': _('You are trying to concile more than the residual of the document')}
            }

        if self.amount_to_concile < 0:

            self.amount_to_concile = 0

            return{

                'warning': {'title': _('User Error!'), 'message': _('Negative amounts are not allowed')}
            }

current_account_imputation_wizard_credit_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
