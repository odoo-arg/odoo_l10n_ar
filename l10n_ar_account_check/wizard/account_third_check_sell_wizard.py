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
from openerp import netsvc
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)

class AccountThirdCheckSellWizard(models.TransientModel):

    _name = "account.third.check.sell.wizard"

    def _get_default_amount(self):

        active_ids = self.env.context.get('active_ids')
        amount = 0

        for check in self.env['account.third.check'].browse(active_ids):

            amount += check.amount

        return amount

    bank_account_id = fields.Many2one('res.partner.bank', 'Cuenta bancaria')
    partner_id = fields.Many2one('res.partner', 'Partner')
    journal_id = fields.Many2one('account.journal', 'Diario', domain=[('type','in',('cash', 'bank'))], required=True)
    account_id = fields.Many2one('account.account', 'Cuenta para la acreditacion del dinero', domain=[('type', '!=', 'view')], required=True)
    date = fields.Date('Fecha de la operacion', required=True)
    commission = fields.Float('Importe de la comision')
    interests = fields.Float('Importe de los intereses')
    initial_amount = fields.Float('Importe inicial', default=_get_default_amount)
    amount = fields.Float('Total a cobrar', compute='_get_amount', readonly=True)
    company_id = fields.Many2one('res.company', 'Compania')
    commission_account_id = fields.Many2one('account.account', 'Cuenta para las comisiones', domain=[('type', '!=', 'view')])
    interest_account_id = fields.Many2one('account.account', 'Cuenta para los intereses', domain=[('type', '!=', 'view')])

    _defaults = {

        'company_id': lambda self,cr,uid,c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
     }

    @api.depends('commission', 'interests')
    def _get_amount(self):

        self.amount = self.initial_amount - self.interests - self.commission

    ''' Crea un documento nuevo con los parametros del wizard
    :returns: Form view del documento
    '''
    @api.multi
    def create_sell_check_document(self):

        sold_check_proxy = self.env['account.sold.check']
        third_check_proxy = self.env['account.third.check']
        wf_service = netsvc.LocalService('workflow')
        move_line = self.env['account.move.line']
        period_id = self.env['account.period'].find(self.date)
        active_ids = self.env.context.get('active_ids', [])

        if period_id:

            period_id = period_id[0]

        if (self.interests < 0 or self.commission < 0):
            raise Warning("Los importes de las intereses y comisiones deben ser positivos")

        checks = third_check_proxy.browse(active_ids)
        company_id = self.company_id.id
        account_check_id = self._get_source_account_check(company_id)
        third_checks = []
        sequence = self.env['ir.sequence'].get('account.sold.check.sequence')

        sold_check = sold_check_proxy.create({
            'name': sequence,
            'date': self.date,
            'commission': self.commission,
            'interests': self.interests,
            'amount': self.amount,
            'partner_id': self.partner_id.id,
            'bank_account_id': self.bank_account_id.id,
            'state': 'sold',
        })

        for check in checks:

            if check.state != 'wallet':
                raise Warning("Los cheques seleccionados deben estar en cartera. \n El cheque "+check.number +" no esta en cartera", )

            wf_service.trg_validate(self.env.uid, 'account.third.check', check.id, 'cartera_deposited', self.env.cr)

            check.write({'sold_check_id': sold_check.id, 'deposit_date': self.date})
            third_checks.append(check.id)

        move_id = self.env['account.move'].create({
            'name': sequence,
            'journal_id': self.journal_id.id,
            'state': 'draft',
            'period_id': period_id.id,
            'date': self.date,
            'ref': _('Venta cheques: %s') % sequence,
        })

        sold_check.write({'account_move_id': move_id.id})

        move_line.create({
            'name': sequence,
            'centralisation': 'normal',
            'account_id': self.account_id.id,
            'move_id': move_id.id,
            'journal_id': self.journal_id.id,
            'period_id': period_id.id,
            'date': self.date,
            'debit': self.amount,
            'credit': 0.0,
            'ref': _('Venta cheques: %s') % sequence,
            'state': 'valid',
        })

        if self.commission:

            move_line.create({
                'name': sequence,
                'centralisation': 'normal',
                'account_id': self.commission_account_id.id,
                'move_id': move_id.id,
                'journal_id': self.journal_id.id,
                'period_id': period_id.id,
                'date': self.date,
                'debit': self.commission,
                'credit': 0.0,
                'ref': _('Comisiones venta cheques: %s') % sequence,
                'state': 'valid',
            })

        if self.interests:

            move_line.create({
                'name': sequence,
                'centralisation': 'normal',
                'account_id': self.interest_account_id.id,
                'move_id': move_id.id,
                'journal_id': self.journal_id.id,
                'period_id': period_id.id,
                'date': self.date,
                'debit': self.interests,
                'credit': 0.0,
                'ref': _('Intereses venta cheques: %s') % sequence,
                'state': 'valid',
            })

        move_line.create({
            'name': sequence,
            'centralisation': 'normal',
            'account_id': account_check_id.id,
            'move_id': move_id.id,
            'journal_id': self.journal_id.id,
            'period_id': period_id.id,
            'date': self.date,
            'debit': 0.0,
            'credit': self.initial_amount,
            'ref': _('Venta cheques: %s') % sequence,
            'state': 'valid',
        })

        move_id.post()

        return { 'type': 'ir.actions.act_window_close' }

    def _get_source_account_check(self, company_id):
        check_config_obj = self.env['account.check.config']

        res = check_config_obj.search([('company_id', '=', company_id)])

        if not res:
            raise Warning('No hay configuración de cheques para esta companía!')

        return res[0].account_id


AccountThirdCheckSellWizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
