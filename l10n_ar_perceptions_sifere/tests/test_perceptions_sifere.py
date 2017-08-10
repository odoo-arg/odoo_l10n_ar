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
from datetime import datetime
from odoo.tests import common


class TestPerceptionsSifere(common.TransactionCase):
    def setUp(self):
        super(TestPerceptionsSifere, self).setUp()
        self.perception_sifere = self.env['perception.sifere'].create({
            'name': 'SIFERE',
            'date_from': datetime.now(),
            'date_to': datetime.now(),
        })

    # TODO

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
