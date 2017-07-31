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

from openerp import models, api
from openerp.exceptions import Warning
from odoo_openpyme_api.padron import banks


class Bank(models.Model):
    _inherit = 'res.bank'

    @api.model
    def update_module(self):
        try:
            self.update_banks()
        except:
            pass

    def update_banks(self):
        """ Actualiza o crea los bancos de argentina segun los registros de AFIP """
        banks_class = banks.Banks
        try:
            data_get = banks_class.get_values(banks_class.get_banks_list())
        except:
            raise Warning("ERROR\nSe ha producido un error al intentar descargar los "
                          "bancos desde el servidor de AFIP. Inténtelo más tarde")

        afip_banks = {element.get('code'): element.get('name') for element in data_get}

        # Traigo los bancos de Argentina de la base
        ar_country = self.env.ref('base.ar')
        bank_proxy = self.env['res.bank']
        base_banks = bank_proxy.search([('country', '=', ar_country.id)])

        # Recorro el diccionario de bancos. Si encuentro el codigo en los que existen en el
        # sistema, sobreescribo el nombre, sino lo creo.
        for key, value in afip_banks.iteritems():
            bank_to_update = base_banks.filtered(lambda r: r.bic == key)
            if bank_to_update:
                bank_to_update.write({'name': value})
            else:
                bank_proxy.create({'name': value, 'bic': key, 'country': ar_country.id})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
