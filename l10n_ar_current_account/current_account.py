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
from openerp.exceptions import except_orm
import logging
_logger = logging.getLogger(__name__)

class current_account(models.TransientModel):

    _name = "current.account"

    partner_id = fields.Many2one('res.partner', 'Partner')
    doc_type = fields.Selection((('fcc', 'FCC'), ('ncc', 'NCC'), ('ndc', 'NDC'),
                                ('fcp', 'FCP'), ('ncp', 'NCP'), ('ndp', 'NDP'),
                                ('rec', 'REC'), ('op', 'OP'), ('otro', 'OTRO')), 'Type')
    denomination = fields.Char('Denomination')
    name = fields.Char('Number')
    date = fields.Date('Date')
    residual = fields.Float('Residual')
    subtotal = fields.Float('Subtotal')
    total = fields.Float('Total')
    state = fields.Selection((('open', 'Open'), ('conciled', 'Conciled')), 'State')
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    voucher_id = fields.Many2one('account.voucher', 'Voucher')
    wizard_id = fields.Integer('Wizard')
    move_line_id = fields.Many2one('account.move.line', 'Linea del asiento')
    due_date = fields.Date(related='move_line_id.date_maturity', string='Fecha de vencimiento')
    
    _order = "date asc"

    """ Function to raise the wizard to concile documents

    :returns: Form view of the wizard
    """
    @api.multi
    def raise_imputation_wizard(self):

        active_ids = self.env.context.get('active_ids')
        wizard_obj = self.env['current.account.imputation.wizard']
        debit_line_obj = self.env['current.account.imputation.wizard.debit.line']
        credit_line_obj = self.env['current.account.imputation.wizard.credit.line']
        wizard = wizard_obj.create({'partner_id': self.partner_id.id})
        credit_residual = 0

        for document in self.browse(active_ids):

            if document.denomination:

                doc_name = document.doc_type.upper() + ' ' + document.denomination

            else:

                doc_name = document.doc_type.upper()

            if document.residual == 0:

                raise except_orm(_('Error!'), _('One of the documents is already conciled, please unconcile first!'))

            if document.residual < 0:

                credit_line_obj.create({'document': doc_name,
                                        'document_number': document.name,
                                        'amount_total': -document.total,
                                        'residual': -document.residual,
                                        'imputation_id': wizard.id,
                                        'move_line_id': document.move_line_id.id,
                })

                credit_residual -= document.residual

            elif document.residual > 0:

                debit_line_obj.create({ 'document': doc_name,
                                        'document_number': document.name,
                                        'amount_total': document.total,
                                        'residual': document.residual,
                                        'imputation_id': wizard.id,
                                        'move_line_id': document.move_line_id.id
                })

        
        debit_residual = 0
        wizard_credit_residual = 0
        
        for debit_line in wizard.imputation_debit_lines:

            debit_residual += debit_line.residual
             
            if credit_residual > 0:
  
                if debit_line.residual <= credit_residual:
  
                    debit_line.amount_to_concile = debit_line.residual
                    credit_residual -= debit_line.residual
                    wizard_credit_residual += debit_line.residual
  
                else:
  
                    debit_line.amount_to_concile = credit_residual
                    wizard_credit_residual += credit_residual           
                    credit_residual = 0
                            
        for credit_line in wizard.imputation_credit_lines:
             
            if debit_residual > 0:
                 
                if credit_line.residual <= debit_residual:
  
                    credit_line.amount_to_concile = credit_line.residual
                    debit_residual -= credit_line.residual
  
                else:
  
                    credit_line.amount_to_concile = debit_residual
                    debit_residual = 0

        wizard.credit_residual = wizard_credit_residual                                        
        wizard.debit_residual = 0
        
        self.wizard_id = wizard.id

        return True

current_account()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
