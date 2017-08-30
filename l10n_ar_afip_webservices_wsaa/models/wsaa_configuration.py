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

from openerp import models, fields
from l10n_ar_api.afip_webservices.wsaa import certificate
from openerp.exceptions import ValidationError


class WsaaConfiguration(models.Model):

    _name = 'wsaa.configuration'

    name = fields.Char('Nombre', required=True)
    type = fields.Selection([
            ('homologation', 'Homologacion'),
            ('production', 'Produccion')
        ],
        'Tipo',
        required=True
    )
    private_key = fields.Text('Llave privada')
    certificate_request = fields.Text('Pedido de certificado')
    certificate = fields.Text('Certificado')
    wsaa_token_ids = fields.One2many('wsaa.token', 'wsaa_configuration_id', 'Tokens')
    company_id = fields.Many2one(
        'res.company',
        'Empresa',
        required=True,
        default=lambda self: self.env.user.company_id.id
    )

    def generate_certificate_request(self):
        """ Genera un nuevo pedido de certificado con la key configurada """

        if not self.private_key:
            raise ValidationError("Falta configurar la clave privada")

        # Seteamos los valores necesarios para la generacion del pedido de certificado
        req = certificate.WsaaCertificate(self.private_key)
        req.country_code = self.company_id.country_id.code
        req.state_name = self.company_id.state_id.name
        req.company_name = self.company_id.name

        if self.company_id.partner_id.vat:
            req.company_vat = 'CUIT {cuit}'.format(cuit=self.company_id.partner_id.vat)
        try:
            certificate_request = req.generate_certificate_request(),
        except AttributeError, e:
            raise ValidationError(e.message)

        self.write({
            'certificate_request': certificate_request[0],
            'certificate': None
        })

    def generate_private_key(self):
        """ Genera una nueva clave privada y borra los parametros de configuacion viejos """

        pk = certificate.WsaaPrivateKey()
        pk.generate_rsa_key()
        self.write({
            'private_key': pk.key,
            'certificate_request': None,
            'certificate': None
        })


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
