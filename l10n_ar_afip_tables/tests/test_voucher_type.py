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

class TestVoucherType(common.TransactionCase): 

    def setUp(self):
        super(TestVoucherType, self).setUp()
        self.voucher_type_test = self.env['afip.voucher.type'].create({
            'name': 'Denominacion',
            'code': '1832'
        })
        
    def test_unique_voucher_type(self):
        self.assertRaises(
            Exception, 
            self.env['afip.voucher.type'].create, 
            {'code': '1832'}
        )

            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: