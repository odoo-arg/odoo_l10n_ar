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
import pytz

from openerp import models, fields, api
from datetime import datetime, timedelta
from odoo_openpyme_api.afip_webservices import wsaa
from openerp.exceptions import ValidationError
from openerp import SUPERUSER_ID


class WsaaToken(models.Model):

    _name = 'wsaa.token'

    name = fields.Char('Servicio', required=True)
    expiration_time = fields.Datetime('Fecha de expiracion')
    token = fields.Text('Token', readonly=True)
    sign = fields.Text('Sign', readonly=True)
    wsaa_configuration_id = fields.Many2one('wsaa.configuration', 'Configuracion', required=True)

    @api.multi
    def action_renew(self, context=None, delta_time_for_expiration=10):
        """ Renueva o crea el ticket de acceso si esta vencido o no creado """

        for token in self:

            renew = True
            if token.expiration_time:
                expiration_time = datetime.strptime(token.expiration_time, '%Y-%m-%d %H:%M:%S')

                # Si faltan mas de X minutos para que el ticket expire no se lo renueva
                if datetime.now() + timedelta(minutes=delta_time_for_expiration) < expiration_time:
                    renew = False

            if renew:
                token._renew_ticket()

    def _renew_ticket(self):
        """ Renueva o crea el ticket de acceso si esta vencido o no creado """

        if not (self.wsaa_configuration_id.certificate and self.wsaa_configuration_id.private_key):
            raise ValidationError("Falta configurar certificado o clave privada")

        # Traemos el timezone
        user = self.env['res.users'].sudo().browse(SUPERUSER_ID)
        tz = pytz.timezone(user.partner_id.tz) if user.partner_id.tz else pytz.utc

        # Creamos el token nuevo para el servicio especificado y lo firmamos con la clave y certificado
        token = wsaa.tokens.AccessRequerimentToken(self.name, tz)
        homologation = False if self.wsaa_configuration_id.type == 'production' else True

        try:
            signed_tra = token.sign_tra(self.wsaa_configuration_id.private_key, self.wsaa_configuration_id.certificate)
            # Hacemos el logeo y obtenemos sus datos
            login_fault = wsaa.wsaa.Wsaa(homologation).login(signed_tra)
        except Exception, e:
            raise ValidationError(e.message)

        access_token = wsaa.tokens.AccessToken()
        access_token.create_token_from_login(login_fault)

        # Pegamos los datos del acceso al ticket
        self.sudo().write({
            'expiration_time': access_token.expiration_time,
            'token': access_token.token,
            'sign': access_token.sign,
        })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
