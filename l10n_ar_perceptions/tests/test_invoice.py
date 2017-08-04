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


class TestInvoice(common.TransactionCase):
    def setUp(self):
        super(TestInvoice, self).setUp()
        self.partner_ri = self.env['res.partner'].create({
            'name': 'Customer',
            'customer': True,
            'supplier': True,
            'property_account_position_id': self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari')
        })
        account = self.partner_ri.property_account_receivable_id
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner_ri.id,
            'fiscal_position_id': self.partner_ri.property_account_position_id.id,
            'account_id': account.id,
            'type': 'in_invoice',
            'state': 'draft'
        })
        self.env['account.invoice.line'].create({
            'name': 'Producto',
            'account_id': account.id,
            'quantity': 1,
            'price_unit': 2000,
            'invoice_id': self.invoice.id,
        })
        self.perception = self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iibb_pba_sufrida').id,
            'invoice_id': self.invoice.id,
            'amount': 20,
            'base': 2000,
            'jurisdiction': 'municipal',
            'name': 'percepcion'
        })

    def test_invoice_perception_onchange(self):
        self.perception.onchange_perception_id()
        assert self.perception.jurisdiction == self.perception.perception_id.jurisdiction
        assert self.perception.name == self.perception.perception_id.name

        perception_new = self.env['account.invoice.perception'].new(self.perception.read()[0])
        perception_new.perception_id = None
        perception_new.onchange_perception_id()
        assert not perception_new.jurisdiction
        assert not perception_new.name

        self.invoice.onchange_perception_ids()

    def test_perception_values(self):
        perception_values = self.invoice._get_perception_tax_vals(self.perception)
        # Nos aseguramos que el diccionario tenga todos los valores necesarios
        assert perception_values.get('base') == 2000
        assert perception_values.get('amount') == 20
        assert perception_values.get('account_id') == self.perception.perception_id.tax_id.account_id.id
        assert perception_values.get('refund_account_id') == self.perception.perception_id.tax_id.refund_account_id.id
        assert perception_values.get('id') == self.perception.perception_id.tax_id.id
        assert self.invoice.get_taxes_values()

    def test_multiple_perceptions_values(self):
        self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iva_sufrida').id,
            'invoice_id': self.invoice.id,
            'amount': 10,
            'base': 1000,
            'jurisdiction': 'nacional',
            'name': 'percepcion iva'
        })
        self.invoice.get_taxes_values()

    def test_multiple_perceptions_of_same_perception_id(self):
        self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iibb_pba_sufrida').id,
            'invoice_id': self.invoice.id,
            'amount': 10,
            'base': 1000,
            'jurisdiction': 'nacional',
            'name': 'percepcion pba'
        })
        # La key contiene el siguiente formato
        vals_key = str(self.perception.perception_id.tax_id.id) + '-' + \
                   str(self.perception.perception_id.tax_id.account_id.id) + '-' + \
                   str(False)

        tax_values = self.invoice.get_taxes_values()
        # Deberia haber una sola con esa key y los valores sumados
        assert tax_values.get(vals_key).get('amount') == 30
        assert tax_values.get(vals_key).get('base') == 3000
        assert tax_values.get(vals_key).get('tax_id') == self.perception.perception_id.tax_id.id
        assert tax_values.get(vals_key).get('account_id') == self.perception.perception_id.tax_id.account_id.id

    def test_refund(self):
        # Como es une one2many tiene el formato [(0,0, {vals})]
        values = self.invoice._prepare_refund(self.invoice).get('perception_ids')[0][2]
        assert values.get('base') == 2000
        assert values.get('amount') == 20
        assert values.get('perception_id') == self.perception.perception_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
