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
from openerp.exceptions import Warning
import socket


class TestL10nAr(common.TransactionCase):

    def setUp(self):
        super(TestL10nAr, self).setUp()
        self.account_tax_template = self.env['account.tax.template'].search([('is_exempt', '=', True)], limit=1)
        self.country_ar = self.env.ref('base.ar')
        self.bank_proxy = self.env['res.bank']

    @staticmethod
    def guard(*args, **kwargs):
        raise Exception("Internet deshabilitado!")

    def test_get_tax_vals(self):
        vals = self.account_tax_template._get_tax_vals(self.env.user.company_id)
        assert vals.get('is_exempt')

    def test_no_conectivity(self):
        original_socket = socket.socket
        socket.socket = self.guard
        with self.assertRaises(Warning):
            self.bank_proxy.update_banks()

        # Cuando actualizamos el modulo no deberia levantar el Warning
        self.bank_proxy.update_module()

        socket.socket = original_socket

    def test_update_banks(self):
        self.bank_proxy.update_banks()
        # Buscamos el nacion
        nacion = self.bank_proxy.search([('bic', '=', '11'), ('country', '=', self.country_ar.id)], limit=1)
        assert nacion
        nacion_name = nacion.name
        # Corremos de vuelta para comprobar los casos de escritura de los que ya existen
        self.bank_proxy.update_banks()
        nacion = self.bank_proxy.search([('bic', '=', '11'), ('country', '=', self.country_ar.id)], limit=1)
        assert nacion_name == nacion.name

    def test_update_banks_module(self):
        self.bank_proxy.update_module()
        # Buscamos el nacion
        assert self.bank_proxy.search([('bic', '=', '11'), ('country', '=', self.country_ar.id)], limit=1)

    def test_update_banks_wizard(self):
        self.env['update.banks.wizard'].action_update()

    def test_create_bank(self):
        self.bank_proxy.search([('bic', '=', '11'), ('country', '=', self.country_ar.id)]).unlink()
        self.bank_proxy.update_banks()
        assert self.bank_proxy.search_count([('bic', '=', '11'), ('country', '=', self.country_ar.id)])

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
