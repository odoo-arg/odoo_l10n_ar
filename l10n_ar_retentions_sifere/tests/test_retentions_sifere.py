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
from datetime import datetime, timedelta, date

import pytest
from odoo.tests import common

from odoo_openpyme_api.presentations import presentation


class TestRetentionsSifere(common.TransactionCase):
    # -------------------------------------------------------------------------
    # AUX
    # -------------------------------------------------------------------------
    def create_payment_data(self):
        self.pos = self.env['pos.ar'].create({
            'name': "4",
        })
        self.partner = self.env['res.partner'].create({
            'name': "Proveedor",
            'country_id': self.country.id,
            'vat': '11222222223',
        })
        self.payment_method = self.env['account.payment.method'].create({
            'name': "Metodo de pago",
            'code': "METODO",
            'payment_type': 'inbound',
        })
        self.payment = self.env['account.payment'].create({
            'partner_id': self.partner.id,
            'payment_type': 'inbound',
            'name': '9999-77777777',
            'payment_method_id': self.payment_method.id,
            'pos_ar_id': self.pos.id,
            'amount': 1000,
        })

    def create_tax_data(self):
        self.tax = self.env['account.tax'].create({
            'name': "SIFERE",
            'amount': 1,
        })
        self.retention = self.env['retention.retention'].create({
            'name': "SIFERE",
            'tax_id': self.tax.id,
            'type': 'gross_income',
            'jurisdiction': 'nacional',
            'state_id': 553,
        })

    def create_country(self):
        self.country = self.env['res.country'].create({
            'name': "Pais",
            'code': "ZZ",
            'no_prefix': True,
        })

    def create_retention(self):
        self.retention_sifere = self.env['retention.sifere'].create({
            'name': "Retencion SIFERE",
            'date_from': datetime.now() - timedelta(days=1),
            'date_to': datetime.now() + timedelta(days=1),
        })
        self.retention_line = self.env['account.payment.retention'].create({
            'name': "Linea Retencion",
            'payment_id': self.payment.id,
            'retention_id': self.retention.id,
            'amount': 400,
            'jurisdiction': 'nacional',
            'create_date': date.today(),
            'certificate_no': "10",
        })
        self.lines = presentation.Presentation("sifere", "retenciones")
        self.code = self.retention_sifere.get_code(self.retention_line)

    # -------------------------------------------------------------------------
    # SETUP
    # -------------------------------------------------------------------------
    def setUp(self, *args, **kwargs):
        super(TestRetentionsSifere, self).setUp(*args, **kwargs)
        self.create_country()
        self.create_tax_data()
        self.create_payment_data()
        self.create_retention()

    # -------------------------------------------------------------------------
    # TESTS
    # -------------------------------------------------------------------------
    def test_retention(self):
        self.retention_sifere.create_line(self.code, self.lines, self.retention_line)
        today = date.today().strftime("%d/%m/%Y")
        assert self.lines.lines[0].get_line_string() == "90211-22222222-3{}00040000000000000010R 000000009999777777770,000,000,400".format(today)

    def test_retention_no_vat(self):
        self.partner.vat = None
        self.retention_sifere.create_line(self.code, self.lines, self.retention_line)
        today = date.today().strftime("%d/%m/%Y")
        assert self.lines.lines[0].get_line_string() == "90200-00000000-0{}00040000000000000010R 000000009999777777770,000,000,400".format(today)

    def test_retention_no_code_exception(self):
        self.code = None
        with pytest.raises(Exception):
            self.retention_sifere.create_line(self.code, self.lines, self.retention_line)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
