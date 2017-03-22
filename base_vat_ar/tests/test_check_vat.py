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
from openerp.exceptions import ValidationError

class TestCheckVat(common.TransactionCase): 

    def setUp(self):
        super(TestCheckVat, self).setUp()
        country_ar = self.env.ref('base.ar')
        self.partner_document_type = self.env['partner.document.type'].create({
            'name': 'CUIT',
            'verification_required': True,
        })
        
        self.partner = self.env['res.partner'].create({
            'name': 'test',
            'country_id': country_ar.id,
            'partner_document_type_id': self.partner_document_type.id,
            'vat': '30709653543',
        })

    def test_vat_ar(self):
        self.partner.check_vat()
        
    def test_invalid_vat(self):
        with self.assertRaises(ValidationError):
            self.partner.vat = '30709653542'
        with self.assertRaises(ValidationError):
            self.partner.vat = '30703542'

    def test_no_check(self):
        self.partner_document_type.verification_required = False
        self.partner.vat = '30703542'
        self.partner.check_vat()
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: