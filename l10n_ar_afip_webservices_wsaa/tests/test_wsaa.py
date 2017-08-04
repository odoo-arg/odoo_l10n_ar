
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


class TestWsaa(common.TransactionCase):

    def setUp(self):
        super(TestWsaa, self).setUp()
        self.wsaa = self.env['wsaa.configuration'].create({
            'type': 'homologation',
            'name': 'wsaa',
        })

    def test_generate_certificate_no_key(self):
        with self.assertRaises(ValidationError):
            self.wsaa.generate_certificate_request()

    def test_generate_key(self):
        self.wsaa.generate_private_key()
        assert self.wsaa.private_key

    def test_generate_certificate(self):
        """ Probamos crear un certificado luego de generar la key """
        self.wsaa.generate_private_key()
        # Deberia estar configurado Codigo de pais, provincia, nombre de la empersa y CUIT de la empresa

        # Sin parametros configurado
        with self.assertRaises(ValidationError):
            self.wsaa.generate_certificate_request()

        # Asignamos el cuit
        self.wsaa.company_id.partner_id.vat = 20000000006
        with self.assertRaises(ValidationError):
            self.wsaa.generate_certificate_request()

        # Asignamos el pais
        self.wsaa.company_id.country_id = self.env.ref('base.ar').id
        with self.assertRaises(ValidationError):
            self.wsaa.generate_certificate_request()

        # Asignamos la pronvicia
        self.wsaa.company_id.state_id = self.env.ref('base.state_ar_c').id

        # Deberiamos poder crear el pedido de certificado correctamente
        self.wsaa.generate_certificate_request()
        assert self.wsaa.certificate_request

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
