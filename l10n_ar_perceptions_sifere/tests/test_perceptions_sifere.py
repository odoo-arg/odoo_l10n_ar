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
from datetime import datetime
from odoo.tests import common


class TestPerceptionsSifere(common.TransactionCase):
    def setUp(self):
        super(TestPerceptionsSifere, self).setUp()
        self.country = self.env['res.country'].create({
            'name': "Pais",
            'code': "ZZ",
        })
        self.tax = self.env['account.tax'].create({
            'name': "SIFERE",
            'amount': 1
        })
        self.perception = self.env['perception.perception'].create({
            'name': "SIFERE",
            'tax_id': self.tax.id,
            'type': 'gross_income',
            'jurisdiction': 'nacional'
        })
        self.partner = self.env['res.partner'].create({
            'name': "Cliente",
            'country_id': self.country.id,
        })
        self.account_type = self.env['account.account.type'].create({
            'name': "Tipo de cuenta",
        })
        self.account = self.env['account.account'].create({
            'code': "Codigo",
            'name': "Cuenta",
            'user_type_id': self.account_type.id,
        })
        self.journal = self.env['account.journal'].create({
            'name': "Diario",
            'type': 'sale',
            'code': "DIA",
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.account.id,
            'journal_id': self.journal.id,
        })

    def test_perception(self):
        self.env['account.invoice.perception'].create({
            'name': "Linea Percepcion",
            'invoice_id': self.invoice.id,
            'perception_id': self.perception.id,
            'amount': 400,
            'jurisdiction': 'nacional',
        })
        assert len(self.invoice.perception_ids) == 1




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
