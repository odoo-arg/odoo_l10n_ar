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
from openerp import netsvc

class AccountSoldCheck(models.Model):

    _name = "account.sold.check"

    name = fields.Char('Documento', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    bank_account_id = fields.Many2one('res.partner.bank', 'Cuenta bancaria', readonly=True)
    date = fields.Date('Fecha de emision')
    commission = fields.Float('Importe de la comision', readonly=True)
    interests = fields.Float('Importe de los intereses', readonly=True)
    amount = fields.Float('Total cobrado', readonly=True)
    account_third_check_ids = fields.One2many('account.third.check', 'sold_check_id', string='Cheques', readonly=True)
    account_move_id = fields.Many2one('account.move', 'Asiento contable', readonly=True)
    state = fields.Selection([('canceled', 'Cancelado'), ('sold', 'Vendido')], string='Estado', readonly=True)
    company_id = fields.Many2one('res.company', 'Compania')
    reject_account_id = fields.Many2one('account.account', 'Cuenta de rechazo')
    
    _defaults = {

        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
     }

    _sql_constraints = [('name_uniq','unique(name)','The name must be unique!')]

    _order = "date desc, name desc"

    ''' Anula el documento, volviendo a cartera los cheques
    '''
    @api.one
    def cancel_sell_check_document(self):
        if not self.account_move_id:

            raise Warning('No hay un asiento relacionado al documento')

        self.account_move_id.button_cancel()
        self.account_move_id.unlink()

        wf_service = netsvc.LocalService('workflow')

        for check in self.account_third_check_ids:

            if check.state != 'deposited':

                raise Warning('El cheque '+check.number+' no se encuentra en estado depositado')

            check.sold_check_id = False
            check.deposit_date = False
            wf_service.trg_validate(self.env.uid, 'account.third.check', check.id, 'deposited_cartera', self.env.cr)

        self.state = 'canceled'

AccountSoldCheck()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
