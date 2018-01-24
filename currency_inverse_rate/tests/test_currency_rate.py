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

from odoo.tests import common
from openerp import fields


class TestCurrencyRate(common.TransactionCase):

    def setUp(self):
        rate = 30
        super(TestCurrencyRate, self).setUp()
        self.currency_rate = self.env['res.currency.rate'].create({
            'name': fields.Datetime.now(),
            'currency_id': self.env.ref('base.USD').id,
            'inverse_rate': rate,
            'rate': 1/rate,
        })

    def test_onchange_rate(self):
        self.currency_rate.currency_id.editable_inverse_rate = False
        self.currency_rate.rate = 0.25
        self.currency_rate.onchange_rate()
        assert self.currency_rate.inverse_rate == 4

    def test_onchange_rate_0(self):
        self.currency_rate.currency_id.editable_inverse_rate = False
        self.currency_rate.rate = 0
        self.currency_rate.onchange_rate()
        assert self.currency_rate.inverse_rate == 0

    def test_onchange_inverse_rate(self):
        self.currency_rate.currency_id.editable_inverse_rate = True
        self.currency_rate.inverse_rate = 0.20
        self.currency_rate.onchange_rate()
        assert self.currency_rate.rate == 5

    def test_onchange_inverse_rate_0(self):
        self.currency_rate.currency_id.editable_inverse_rate = True
        self.currency_rate.inverse_rate = 0
        self.currency_rate.onchange_rate()
        assert self.currency_rate.rate == 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
