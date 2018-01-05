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

import test_checkbook
from datetime import date


class TestAccountCheckCollectWizard(test_checkbook.TestCheckbook):

    def setUp(self):
        super(TestAccountCheckCollectWizard, self).setUp()
        own_check_proxy = self.env['account.own.check']
        self.own_check = own_check_proxy.create({
            'name': '12345678',
            'bank_id': self.env['res.bank'].search([], limit=1).id,
            'payment_type': 'common',
            'checkbook_id': self.checkbook.id
        })

        collect_wizard_proxy = self.env['account.check.collect.wizard']

        self.collect_wizard = collect_wizard_proxy.create({
            'amount': 200.0,
            'account_id': self.env['account.account'].search([], limit=1).id,
            'journal_id': self.env['account.journal'].search([], limit=1).id,
            'payment_date': date.today(),
            'collect_date': date.today(),
            'issue_date': date.today(),
        })

    def test_collect_check(self):

        ctx = self.env.context.copy()
        ctx.update({'active_id': self.own_check.id})
        self.collect_wizard.with_context(ctx).collect_check()
        assert self.own_check.amount == 200.0
        assert self.own_check.state == 'collect'

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
