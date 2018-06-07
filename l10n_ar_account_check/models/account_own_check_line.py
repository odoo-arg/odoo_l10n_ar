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
from openerp.exceptions import ValidationError


class AccountOwnCheckLine(models.Model):
    _name = 'account.own.check.line'

    checkbook_id = fields.Many2one('account.checkbook', 'Chequera')
    own_check_id = fields.Many2one('account.own.check', 'Cheque', required=True)
    issue_date = fields.Date('Fecha de emision')
    payment_date = fields.Date('Fecha de pago')
    payment_type = fields.Selection(
        [('common', 'Comun'),
         ('postdated', 'Diferido')],
        string="Tipo",
        related='own_check_id.payment_type'
    )
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('handed', 'Entregado'),
            ('canceled', 'Anulado'),
            ('rejected', 'Rechazado')
        ],
        string='Estado',
        related='own_check_id.state'
    )
    payment_id = fields.Many2one('account.payment', 'Pago', ondelete="cascade")
    amount = fields.Float('Importe', required=True)

    company_id = fields.Many2one('res.company', string='Compania', related='own_check_id.company_id', store=True,
                                 readonly=True, related_sudo=False)

    @api.multi
    def post_payment(self, payment):
        """ Lo que deberia pasar con el cheque cuando se valida el pago.. """

        for own_check_line in self:
            payment_date = own_check_line.issue_date if own_check_line.payment_type == 'common' \
                else own_check_line.payment_date
            vals = {
                'amount': own_check_line.amount,
                'payment_date': payment_date,
                'issue_date': own_check_line.issue_date,
                'destination_payment_id': payment.id,
            }
            own_check_line.own_check_id.post_payment(vals)

    @api.constrains('own_check_id')
    def constraint_own_check(self):
        """ Evitamos que validen dos pagos con el mismo cheque (o dupliquen el cheque en el pago) """
        for check_line in self:
            if check_line.search_count(
                    [('own_check_id', '=', check_line.own_check_id.id), ('payment_id', '!=', False)]) > 1:
                raise ValidationError("El cheque " + check_line.own_check_id.name + " ya existe en un pago")

    @api.onchange('checkbook_id')
    def onchange_checkbook(self):
        self.own_check_id = False
        domain = [
            ('destination_payment_id', '=', False),
            ('state', '=', 'draft'),
        ]

        if self.checkbook_id:
            domain.append(('checkbook_id', '=', self.checkbook_id.id))

        return {'domain': {'own_check_id': domain}}

    @api.onchange('own_check_id')
    def onchange_own_check(self):
        self.update({
            'payment_date': None,
            'issue_date': None,
            'amount': None,
        })

    @api.onchange('issue_date')
    def onchange_issue_date(self):
        if self.own_check_id.payment_type == 'common':
            if self.issue_date:
                self.payment_date = self.issue_date
            else:
                self.payment_date = None

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
