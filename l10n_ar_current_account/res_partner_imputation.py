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

class ResPartnerImputation(models.Model):

    _name = "res.partner.imputation"

    date = fields.Date('Fecha', required=True, readonly=True)
    name = fields.Char ('Nombre', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    number = fields.Integer('Numero', required=True, readonly=True)
    state = fields.Selection((('valid', 'Validado'), ('cancel', 'Cancelado')), 'Estado', required=True, readonly=True)
    move_id = fields.Many2one('account.move', 'Asiento', readonly=True)
    document_imputation_ids = fields.One2many('res.partner.document.imputation', 'imputation_id', 'Documentos', readonly=True)

    @api.one
    def remove_move(self):

        reconcile_pool = self.pool.get('account.move.reconcile')
        move_line_pool = self.pool.get('account.move.line')
        
        for line in self.move_id.line_id:

            line.refresh()
            if line.reconcile_id:            
                
                move_lines = [move_line.id for move_line in line.reconcile_id.line_id]
                move_lines.remove(line.id)
                reconcile_pool.unlink(self.env.cr, self.env.uid, [line.reconcile_id.id])
                if len(move_lines) >= 2:
                    move_line_pool.reconcile_partial(self.env.cr, self.env.uid, move_lines, 'auto',context=self.env.context)
                
        if self.move_id:        
            self.move_id.unlink()
       
        self.state = 'cancel'
                
ResPartnerImputation()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
