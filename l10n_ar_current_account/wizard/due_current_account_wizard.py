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
from openerp.exceptions import Warning

class DueCurrentAccountWizard(models.TransientModel):

    _name = 'due.current.account.wizard'

    due_date_start = fields.Date('Desde')
    due_date_stop = fields.Date('Hasta')
    type = fields.Selection([('customer', 'Clientes'), ('supplier', 'Proveedores')], string="Tipo", required=True)
    
    @api.multi
    def get_all_accounts(self):
        ''' Trae todos los documentos sin imputaciones para clientes o proveedores
        :returns: Vista del objeto current.account con el detalle de los documentos
        '''
        
        move_line_proxy = self.env['account.move.line']        
        current_account_proxy = self.env['current.account']
        res_partner_proxy = self.env['res.partner']
        current_accounts = current_account_proxy.search([])
        current_accounts.unlink()
        dates_domain = []
        
        if self.due_date_start > self.due_date_stop:
            
            raise Warning('La fecha "desde" debe ser menor que la fecha "hasta"')
        
        if self.due_date_start:
            
            dates_domain.append(('date_maturity', '>=', self.due_date_start))
            
        if self.due_date_stop:
            
            dates_domain.append(('date_maturity', '<=', self.due_date_stop))
        
        #TODO: Cambiar el manejo del if else
        if self.type == 'supplier':
            
            for current_supplier in res_partner_proxy.search([('supplier', '=', True)]):
                
                supplier_domain = [
                    ('state', '=', 'valid'), 
                    ('account_id.type', '=', 'payable'), 
                    ('partner_id', '=', current_supplier.id)
                ]
                
                customer_domain = [
                    ('state','=','valid'), 
                    ('account_id.type', '=', 'receivable'), 
                    ('partner_id', '=', current_supplier.id)
                ]
                
                if dates_domain:
                    
                    supplier_domain += (dates_domain)
                    customer_domain += (dates_domain)
                    
                supplier_move_lines = move_line_proxy.search(supplier_domain)
                current_supplier._get_supplier_move_lines(supplier_move_lines=supplier_move_lines)
                
                customer_move_lines = move_line_proxy.search(customer_domain)
                current_supplier._get_supplier_move_lines(customer_move_lines)

        elif self.type == 'customer':
            
            for current_customer in res_partner_proxy.search([('customer', '=', True)]):

                supplier_domain = [
                    ('state', '=', 'valid'), 
                    ('account_id.type', '=', 'payable'), 
                    ('partner_id', '=', current_customer.id)
                ]
                
                customer_domain = [
                    ('state','=','valid'), 
                    ('account_id.type', '=', 'receivable'), 
                    ('partner_id', '=', current_customer.id)
                ]

                if dates_domain:
                    
                    supplier_domain += (dates_domain)
                    customer_domain += (dates_domain)
                                                    
                customer_move_lines = move_line_proxy.search(customer_domain)
                current_customer._get_customer_move_lines(customer_move_lines)
                
                supplier_move_lines = move_line_proxy.search(supplier_domain)
                current_customer._get_customer_move_lines(supplier_move_lines=supplier_move_lines)
                    
        return {

            'name': 'Deudas y documentos sin imputar',
            'views': [[False, "tree"]],
            'domain': [('state', '=', 'open')],
            'res_model': 'current.account',
            'type': 'ir.actions.act_window',
        }
                
        
DueCurrentAccountWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: