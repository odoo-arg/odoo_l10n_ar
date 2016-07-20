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

from openerp import models, api
from openerp.exceptions import Warning

class AccountMove(models.Model):

    _inherit = 'account.move'
    
    @api.multi
    def button_cancel(self):
        
        for move in self:
            
            for line in move.line_id:
                
                if line.is_reconciled:
                    
                    raise Warning('No se puede cancelar un asiento con movimientos\n\
                        conciliados en una conciliacion bancaria')
            
        return super(AccountMove, self).button_cancel()
    
    @api.multi
    def unlink(self):
        
        for move in self:
            
            for line in move.line_id:
                
                if line.is_reconciled:
                    
                    raise Warning('No se puede eliminar un asiento con movimientos\n\
                        conciliados en una conciliacion bancaria')        
           
        return super(AccountMove, self).unlink()
    
AccountMove()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: