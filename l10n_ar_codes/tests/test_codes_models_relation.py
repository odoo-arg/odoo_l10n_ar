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

import pytest
from odoo.tests import common
from openerp.exceptions import Warning


class TestCodesModelsRelation(common.TransactionCase):

    def setUp(self):
        super(TestCodesModelsRelation, self).setUp()
        country_ar = self.env.ref('base.ar')
        self.test_codes_models_country = self.env['codes.models.relation'].create({
            'name': 'test',
            'name_model': 'res.country',
            'id_model': country_ar.id,
            'code': 'x'
        })

    def test_model_attribute(self):
        self.assertEqual(self.test_codes_models_country.get_record().code, 'AR')
        
    def test_invalid_model(self):
        self.test_codes_models_country.name_model = 'res.countri'
        with self.assertRaises(Exception):
            self.test_codes_models_country.get_record()

    def test_invalid_record_id(self):
        self.test_codes_models_country.id_model = None
        with self.assertRaises(Exception):
            self.test_codes_models_country.get_record()

    def test_unique(self):
        country_ar = self.env.ref('base.ar')
        with self.assertRaises(Exception):
            # IntegrityError
            self.env['codes.models.relation'].create({
                'name': 'test',
                'name_model': 'res.country',
                'id_model': country_ar.id,
                'code': 'x'
            })

    def test_get_record_from_code(self):
        with pytest.raises(Warning):
            self.env['codes.models.relation'].get_record_from_code('res.partner', 'x', 'test')

    def test_get_invalid_record_from_code(self):
        assert self.env.ref('base.ar').id ==\
               self.env['codes.models.relation'].get_record_from_code('res.country', 'x', 'test').id

    def test_get_code(self):
        assert 'x' == self.env['codes.models.relation'].get_code('res.country', self.env.ref('base.ar').id, 'test')

    def test_get_invalid_code(self):
        with pytest.raises(Warning):
            self.env['codes.models.relation'].get_code('res.country', -1, 'test')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
