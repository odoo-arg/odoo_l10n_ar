# -*- encoding: utf-8 -*-

from datetime import date


def _assert_header_values(self, header):
    """ Validamos los valores del header en esta funcion para no ensuciar """
    assert header.get(0) == 'Fecha'
    assert header.get(1) == 'Razon Social'
    assert header.get(2) == 'Doc. Numero'
    assert header.get(3) == 'Condicion IVA'
    assert header.get(4) == 'Tipo'
    assert header.get(5) == 'Denominacion'
    assert header.get(6) == 'Numero'
    assert header.get(7) == 'Jurisdiccion'
    assert header.get(8) == self.env.ref('l10n_ar.1_vat_105_ventas').name + ' - Base'
    assert header.get(9) == self.env.ref('l10n_ar.1_vat_105_ventas').name + ' - Importe'
    assert header.get(10) == self.env.ref('l10n_ar.1_vat_21_ventas').name + ' - Base'
    assert header.get(11) == self.env.ref('l10n_ar.1_vat_21_ventas').name + ' - Importe'
    assert header.get(12) == self.env.ref('l10n_ar.1_vat_enard').name
    assert header.get(13) == 'No Gravado'
    assert header.get(14) == 'Total'


def _assert_invoices_values_customer(self, details):
    """ Validamos los valores de varios casos en esta funcion para no ensuciar """
    # Caso de una factura
    assert details[0].get(0) == date.today().replace(day=1).strftime('%d/%m/%Y')
    assert details[0].get(1) == 'Partner'
    assert details[0].get(2) == '30000000003'
    assert details[0].get(3) == self.env.ref('l10n_ar_afip_tables.account_fiscal_position_ivari').name
    assert details[0].get(4) == 'FCC'
    assert details[0].get(5) == 'A'
    assert details[0].get(6) == '0005-00000033'
    assert details[0].get(7) == self.env.ref('base.state_ar_b').name
    assert not details[0].get(8)
    assert not details[0].get(9)
    assert details[0].get(10) == 500
    assert details[0].get(11) == 105
    assert details[0].get(12) == 0
    assert details[0].get(13) == 0
    assert details[0].get(14) == 605


    # Caso de una nota de credito
    assert details[1].get(0) == date.today().replace(day=2).strftime('%d/%m/%Y')
    assert details[1].get(4) == 'NCC'
    assert details[1].get(5) == 'A'
    assert details[1].get(8) == -500
    assert details[1].get(9) == -52.5
    assert not details[1].get(10)
    assert not details[1].get(11)
    assert not details[1].get(12)
    assert details[1].get(13) == 0
    assert details[1].get(14) == -552.5

    # Nota de debito
    assert details[2].get(0) == date.today().replace(day=3).strftime('%d/%m/%Y')
    assert details[2].get(4) == 'NDC'
    assert details[2].get(5) == 'A'
    assert not details[2].get(8)
    assert not details[2].get(9)
    assert not details[2].get(10)
    assert not details[2].get(11)
    assert details[2].get(12) == 0
    assert details[2].get(13) == 500
    assert details[2].get(14) == 500


def _assert_invoices_values_supplier(self, details):
    """ Validamos los valores de varios casos en esta funcion para no ensuciar """
    # Caso de una factura
    assert details[0].get(0) == date.today().replace(day=1).strftime('%d/%m/%Y')
    assert details[0].get(4) == 'FCP'
    assert details[0].get(5) == 'A'
    assert details[0].get(6) == '0001-00000111'
    assert not details[0].get(8)
    assert not details[0].get(9)
    assert details[0].get(10) == 500
    assert details[0].get(11) == 105
    assert details[0].get(12) == 0
    assert details[0].get(13) == 0
    assert details[0].get(14) == 605

    # Caso de una nota de credito
    assert details[1].get(0) == date.today().replace(day=2).strftime('%d/%m/%Y')
    assert details[1].get(4) == 'NCP'
    assert details[1].get(5) == 'A'
    assert details[1].get(8) == -500
    assert details[1].get(9) == -52.5
    assert not details[1].get(10)
    assert not details[1].get(11)
    assert not details[1].get(12)
    assert details[1].get(13) == 0
    assert details[1].get(14) == -552.5

    # Nota de debito
    assert details[2].get(0) == date.today().replace(day=3).strftime('%d/%m/%Y')
    assert details[2].get(4) == 'NDP'
    assert details[2].get(5) == 'A'
    assert not details[2].get(8)
    assert not details[2].get(9)
    assert not details[2].get(10)
    assert not details[2].get(11)
    assert details[2].get(12) == 0
    assert details[2].get(13) == 500
    assert details[2].get(14) == 500

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
