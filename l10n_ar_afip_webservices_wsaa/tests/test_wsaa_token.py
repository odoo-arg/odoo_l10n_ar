
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

from openerp import SUPERUSER_ID
from openerp.exceptions import ValidationError
from test_wsaa import TestWsaa
import config


class TestWsaaToken(TestWsaa):

    def setUp(self):
        super(TestWsaaToken, self).setUp()
        self.wsaa.write({
            'private_key': config.private_key,
            'certificate': config.certificate,
        })
        self.wsaa_token = self.env['wsaa.token'].create({
            'name': 'wsfe',
            'wsaa_configuration_id': self.wsaa.id,
        })
        self.user = self.env['res.users'].sudo().browse(SUPERUSER_ID)
        self.user.partner_id.tz = 'America/Argentina/Buenos_Aires'

    def test_create_ticket_no_certificate_or_pk(self):
        # Probamos crear el ticket sin certificado o clave privada
        self.wsaa.write({
            'private_key': None,
            'certificate': None
        })

        with self.assertRaises(ValidationError):
            self.wsaa_token.action_renew()

        # Asignamos una pk
        self.wsaa.private_key = 'A'
        with self.assertRaises(ValidationError):
            self.wsaa_token.action_renew()

        # Asignamos una certificado y eliminamos la pk
        self.wsaa.certificate = 'A'
        self.wsaa.private_key = None
        with self.assertRaises(ValidationError):
            self.wsaa_token.action_renew()

    def test_invalid_certificate(self):
        self.wsaa.certificate = 'A'
        with self.assertRaises(ValidationError):
            self.wsaa_token.action_renew()

    def test_invalid_private_key(self):
        self.wsaa.private_key = 'A'
        with self.assertRaises(ValidationError):
            self.wsaa_token.action_renew()

    def test_create_ticket(self):
        self.wsaa_token.action_renew()
        assert (self.wsaa_token.expiration_time and self.wsaa_token.token and self.wsaa_token.sign)

    def test_renew_ticket(self):
        assert not self.wsaa_token.expiration_time
        self.wsaa_token.action_renew()
        assert self.wsaa_token.expiration_time
        self.wsaa_token.action_renew()
        assert (self.wsaa_token.expiration_time and self.wsaa_token.token and self.wsaa_token.sign)

    def test_get_access_token(self):
        access_token = self.wsaa_token.get_access_token()
        assert self.wsaa_token.sign == access_token.sign
        assert self.wsaa_token.token == access_token.token

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
