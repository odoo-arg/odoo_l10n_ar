# - coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.tests.common import TransactionCase


class UnitTest(TransactionCase):

    def setUp(self):
        super(UnitTest, self).setUp()
        self.presentation_proxy = self.env['account.invoice.presentation']

    # TESTS
    def test_can_create_a_presentation(self):
        "Se puede crear una presentacion"
        self.presentation_proxy.create({
            'name': 'TEST',
            'date_from': '2017-08-01',
            'date_to': '2017-08-31',
            'sequence': '00',
            'with_prorate': True
        })

    def test_cannot_create_a_presentation_with_bad_dates(self):
        "No se puede generar una presentacion con las fechas mal"
        with self.assertRaises(Exception):
            self.presentation_proxy.create({
                'name': 'TEST',
                'date_from': '2017-08-31',
                'date_to': '2017-08-01',
                'sequence': '00',
                'with_prorate': True
            })

    def test_cannot_generate_presentations_without_vat(self):
        "No se pueden generar las presentaciones sin el CUIT de la compania"
        self.env.user.company_id.partner_id.vat = ""
        presentation = self.presentation_proxy.create({
            'name': 'TEST',
            'date_from': '2017-08-01',
            'date_to': '2017-08-31',
            'sequence': '00',
        })
        with self.assertRaises(Exception):
            presentation.generate_files()

    def test_can_generate_presentations(self):
        "Se pueden generar las presentaciones"
        self.env.user.company_id.partner_id.vat = "20359891033"
        presentation = self.presentation_proxy.create({
            'name': 'TEST',
            'date_from': '2017-08-01',
            'date_to': '2017-08-31',
            'sequence': '00',
        })

        presentation.generate_files()



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
