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

import set_up
from openerp.exceptions import ValidationError, UserError
from mock import mock


class TestAccountPayment(set_up.SetUp):
    def test_payment_type_line_amount(self):
        """ Intentamos cargar una linea de pago con distintos importes """
        self.payment_line.amount = 1000.12
        self.payment_line.amount = 0.1
        with self.assertRaises(ValidationError):
            self.payment_line.amount = 0
        with self.assertRaises(ValidationError):
            self.payment_line.amount = -230.5

    def test_pos(self):
        customer_payment = self.customer_payment.with_context(default_payment_type='inbound')
        supplier_payment = self.customer_payment.with_context(default_payment_type='outbound')

        assert customer_payment._get_default_pos() == self.pos_inbound.id
        assert supplier_payment._get_default_pos() == self.pos_outbound.id

    def test_amount_invoices(self):
        active_model = 'account.invoice'
        active_ids = [self.invoice.id]
        total_invoices = self.customer_payment.with_context(active_model=active_model, active_ids=active_ids). \
            _get_total_invoices_amount_default()
        assert total_invoices == self.invoice.residual

        get_total_invoices = 'odoo.addons.l10n_ar_account_payment.models.account_payment.' \
                             'AccountAbstractPayment._get_total_invoices_amount_default'

        # Mockiamos la funcion porque perdemos el contexto que armamos previo
        with mock.patch(get_total_invoices) as MockClass:
            MockClass.return_value = total_invoices
            self.customer_payment._get_total_invoices_amount()
            assert self.customer_payment.total_invoices_amount == self.invoice.residual

    def test_onchange_payment_line(self):
        self.customer_payment.amount = 10000
        self.customer_payment.onchange_payment_type_line_ids()
        assert self.customer_payment.amount == 500

    def test_onchange_currency_id(self):
        assert self.customer_payment.payment_type_line_ids
        self.customer_payment.onchange_currency_id()
        assert not self.customer_payment.payment_type_line_ids

    def test_get_document_book(self):

        # Sin punto de venta
        with self.assertRaises(ValidationError):
            self.customer_payment.get_document_book()

        self.customer_payment.pos_ar_id = self.pos_inbound
        assert self.customer_payment.get_document_book() == self.document_book_inbound

        self.document_book_inbound.unlink()
        # Sin el talonario
        with self.assertRaises(ValidationError):
            self.customer_payment.get_document_book()

    def test_get_pos(self):
        assert self.customer_payment.get_pos(self.customer_payment.payment_type) == self.pos_inbound.id
        self.document_book_inbound.unlink()
        self.document_book_invoice.unlink()
        self.pos_inbound.unlink()
        assert not self.customer_payment.get_pos(self.customer_payment.payment_type)

    def test_payment_method_vals(self):
        vals = self.customer_payment.set_payment_methods_vals()
        assert vals[0].get('amount') == 500
        assert vals[0].get('account_id') == self.payment_type_transfer.account_id.id

    def test_multiple_payment_methods_vals(self):
        # Creamos una nueva - Efectivo
        payment_type_cash = self.env['account.payment.type'].create({
            'name': 'Efectivo',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
        })
        self.env['account.payment.type.line'].create({
            'account_payment_type_id': payment_type_cash.id,
            'payment_id': self.customer_payment.id,
            'amount': 1000
        })

        vals = self.customer_payment.set_payment_methods_vals()
        vals.sort(key=lambda x: x['amount'])
        assert vals[0].get('amount') == 500
        assert vals[0].get('account_id') == self.payment_type_transfer.account_id.id

        assert vals[1].get('amount') == 1000
        assert vals[1].get('account_id') == payment_type_cash.account_id.id

    def test_grouped_payment_method_vals(self):
        vals = self.customer_payment._get_payment_methods_vals()
        assert vals[0].get('amount') == 500
        assert vals[0].get('account_id') == self.payment_type_transfer.account_id.id

    def test_grouped_multiple_payment_method_vals(self):
        # Agregamos otra transferencia
        self.env['account.payment.type.line'].create({
            'account_payment_type_id': self.payment_type_transfer.id,
            'payment_id': self.customer_payment.id,
            'amount': 2000
        })

        # Creamos una nueva - Efectivo
        payment_type_cash = self.env['account.payment.type'].create({
            'name': 'Efectivo',
            'account_id': self.env.ref('l10n_ar.1_caja_pesos').id,
        })
        self.env['account.payment.type.line'].create({
            'account_payment_type_id': payment_type_cash.id,
            'payment_id': self.customer_payment.id,
            'amount': 1000
        })

        vals = self.customer_payment._get_payment_methods_vals()
        vals.sort(key=lambda x: x['amount'])
        assert vals[0].get('amount') == 1000
        assert vals[0].get('account_id') == payment_type_cash.account_id.id
        assert vals[1].get('amount') == 2500
        assert vals[1].get('account_id') == self.payment_type_transfer.account_id.id

    def test_invalid_account_payment_method(self):
        vals = self.customer_payment.set_payment_methods_vals()
        vals[0].pop('account_id')
        with self.assertRaises(ValidationError):
            self.customer_payment._validate_payment_vals(vals)

    def test_invalid_amount_payment_method(self):
        vals = self.customer_payment.set_payment_methods_vals()
        vals[0].pop('amount')
        with self.assertRaises(ValidationError):
            self.customer_payment._validate_payment_vals(vals)

    def test_onchange_payment_type(self):
        payment = self.env['account.payment'].new({
            'payment_type': 'transfer',
            'pos_ar_id': self.pos_inbound,
            'payment_type_line_ids': [(6, 0, [self.payment_line.id])]
        })
        payment.onchange_payment_type()
        assert not payment.pos_ar_id
        assert not payment.payment_type_line_ids

        payment.payment_type = 'outbound'
        payment.onchange_payment_type()
        assert payment.pos_ar_id == self.pos_outbound

    def test_has_number(self):

        # Previo a validarse no deberia tener nombre
        assert not self.customer_payment.has_number
        # Luego de validarse ya deberia tener el nombre
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.customer_payment.post_l10n_ar()
        self.customer_payment._set_has_number()
        assert self.customer_payment.has_number

    def test_old_post(self):
        """ Validamos que la funcion vieja de post no se pueda ejecutar """
        with self.assertRaises(ValidationError) as e:
            self.customer_payment.post()

        assert str(e.exception[0]) == 'Funcion de validacion de pago estandar deshabilitada'

    def test_unlink(self):
        """ Antes no se podia borrar un pago que alguna vez tuvo numero, en la localizacion si """
        self.customer_payment.pos_ar_id = self.pos_inbound
        self.customer_payment.post_l10n_ar()
        self.customer_payment.cancel()
        self.customer_payment.unlink()

    def test_internal_transfer(self):
        """ Probamos una transferencia entre cuentas internas, la cual deberia funcionar igual que el base """

        self.customer_payment.write({
            'pos_ar_id': self.pos_inbound.id,
            'payment_type': 'transfer',
            'destination_journal_id': self.env.ref('l10n_ar.journal_cobros_y_pagos').id
        })
        self.customer_payment.post_l10n_ar()
        sequence_code = 'account.payment.transfer'
        sequence = self.env['ir.sequence'].with_context(ir_sequence_date=self.customer_payment.payment_date)\
            .next_by_code(sequence_code)
        # Validamos que este tomando la numeracion de la secuencia y el asiento tenga la numeracion del diario
        assert not self.customer_payment.pos_ar_id
        assert self.customer_payment.name == sequence[:-4]+str(int(sequence[-4:])-1).zfill(4)
        assert self.customer_payment.move_name[:3] == 'CYP'

        # Por ultimo validamos que el estado este como pagado
        assert self.customer_payment.state == 'posted'

    def test_outbound_customer(self):
        """ Probamos un caso de pago a un cliente, la cual deberia funcionar igual que el base """

        self.customer_payment.write({
            'pos_ar_id': self.pos_outbound.id,
            'payment_type': 'outbound',
            'destination_journal_id': self.env.ref('l10n_ar.journal_cobros_y_pagos').id
        })
        self.customer_payment.post_l10n_ar()
        sequence_code = 'account.payment.customer.refund'
        sequence = self.env['ir.sequence'].with_context(ir_sequence_date=self.customer_payment.payment_date)\
            .next_by_code(sequence_code)
        assert not self.customer_payment.pos_ar_id
        assert self.customer_payment.name == sequence[:-4]+str(int(sequence[-4:])-1).zfill(4)
        assert self.customer_payment.move_name[:3] == 'CYP'

    def test_inbound_supplier(self):
        """ Probamos un caso de cobro a un proveedor, la cual deberia funcionar igual que el base """

        self.supplier_payment.write({
            'pos_ar_id': self.pos_inbound.id,
            'payment_type': 'inbound',
            'destination_journal_id': self.env.ref('l10n_ar.journal_cobros_y_pagos').id
        })
        self.payment_line.payment_id = self.supplier_payment.id
        self.supplier_payment.post_l10n_ar()
        sequence_code = 'account.payment.supplier.refund'
        sequence = self.env['ir.sequence'].with_context(ir_sequence_date=self.supplier_payment.payment_date)\
            .next_by_code(sequence_code)
        assert not self.supplier_payment.pos_ar_id
        assert self.supplier_payment.name == sequence[:-4]+str(int(sequence[-4:])-1).zfill(4)
        assert self.supplier_payment.move_name[:3] == 'CYP'

    def test_outbound_supplier(self):
        """ Probamos un caso de pago a un proveedor, lo cual deberia usar el punto de venta y talonario """
        self.supplier_payment.pos_ar_id = self.supplier_payment.get_pos(self.supplier_payment.payment_type)
        self.payment_line.payment_id = self.supplier_payment.id
        self.supplier_payment.post_l10n_ar()

        assert self.supplier_payment.pos_ar_id == self.pos_outbound
        payment_name = self.pos_outbound.name.zfill(4)+'-'+self.document_book_outbound.name.zfill(8)

        # Tanto el pago como las lineas de los asientos deberia tener el numero con el formato de payment_name
        move_lines = self.env['account.move.line'].search([('payment_id', '=', self.supplier_payment.id)])
        assert self.supplier_payment.name == payment_name
        assert all(move_line.name == 'OP '+self.supplier_payment.name for move_line in move_lines)

    def test_inbound_customer(self):
        """ Probamos un caso de cobro a un cliente, lo cual deberia usar el punto de venta y talonario """
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.payment_id = self.customer_payment.id
        self.customer_payment.post_l10n_ar()

        assert self.customer_payment.pos_ar_id == self.pos_inbound
        payment_name = self.pos_inbound.name.zfill(4)+'-'+self.document_book_inbound.name.zfill(8)

        # Tanto el pago como las lineas de los asientos deberia tener el numero con el formato de payment_name
        move_lines = self.env['account.move.line'].search([('payment_id', '=', self.customer_payment.id)])
        assert self.customer_payment.name == payment_name
        assert all(move_line.name == 'REC '+self.customer_payment.name for move_line in move_lines)

    def test_payment_with_different_amounts(self):
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'amount': 310
        })
        with self.assertRaises(UserError):
            self.customer_payment.post_l10n_ar()

    def test_payment_name_after_cancel(self):
        """ Validamos que siga el mismo numero y no tome el proximo del talonario si se cancela un pago """
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.payment_id = self.customer_payment.id
        self.customer_payment.post_l10n_ar()

        payment_name = self.customer_payment.name
        self.customer_payment.cancel()
        self.customer_payment.post_l10n_ar()
        assert self.customer_payment.name == payment_name

    def test_invalid_payment_state(self):
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'state': 'posted'
        })
        # Intentamos validar un pago ya validado
        with self.assertRaises(UserError):
            self.customer_payment.post_l10n_ar()

    def test_payment_greater_than_invoice(self):
        """ Validamos que siga funcionando el caso que se pague de mas """
        self.payment_line.amount = 1000
        self.customer_payment.pos_ar_id = self.customer_payment.get_pos(self.customer_payment.payment_type)
        self.customer_payment.payment_id = self.customer_payment.id
        self.customer_payment.onchange_payment_type_line_ids()
        self.customer_payment.post_l10n_ar()

    def test_payment_lesser_than_invoice_customer(self):
        """ Validamos que siga funcionando el caso que se pague menos que el total de la factura """
        self.payment_line.amount = 8000
        self.customer_payment.write({
            'pos_ar_id': self.customer_payment.get_pos(self.customer_payment.payment_type),
            'payment_id': self.customer_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])]
        })
        self.customer_payment.onchange_payment_type_line_ids()
        self.customer_payment.payment_difference_handling = 'reconcile'
        self.customer_payment.writeoff_account_id = self.env.ref('l10n_ar.1_banco').id
        self.customer_payment.post_l10n_ar()

    def test_payment_lesser_than_invoice_supplier(self):
        """ Validamos que siga funcionando el caso que se pague menos que el total de la factura """
        self.payment_line.write({
            'amount': 8000,
            'payment_id': self.supplier_payment.id
        })
        self.invoice.type = 'in_invoice'
        self.supplier_payment.write({
            'pos_ar_id': self.supplier_payment.get_pos(self.supplier_payment.payment_type),
            'payment_id': self.supplier_payment.id,
            'invoice_ids': [(6, 0, [self.invoice.id])]
        })
        self.supplier_payment.onchange_payment_type_line_ids()
        self.supplier_payment.payment_difference_handling = 'reconcile'
        self.supplier_payment.writeoff_account_id = self.env.ref('l10n_ar.1_banco').id
        self.supplier_payment.post_l10n_ar()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
