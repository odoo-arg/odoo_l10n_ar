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

from mock import mock
import set_up
from openerp.exceptions import ValidationError
from odoo.addons.l10n_ar_afip_webservices_wsaa.tests import config


class TestInvoice(set_up.SetUp):

    def test_electronic_invoice_details_fc_a(self):

        document_type_id = self.document_book_fc_a.document_type_id.id
        voucher_type = self.env['afip.voucher.type'].search([
            ('document_type_id', '=', document_type_id),
            ('denomination_id', '=', self.invoice.denomination_id.id)],
            limit=1
        )
        document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))
        assert document_afip_code == 1
        electronic_invoice = self.invoice._set_electronic_invoice_details(document_afip_code)

        # Validamos los montos
        assert electronic_invoice[0].taxed_amount == 1000
        assert electronic_invoice[0].untaxed_amount == 0
        assert electronic_invoice[0].exempt_amount == 0

        # Validamos el array de impuestos (deberia haber 1 iva del 21%)
        assert electronic_invoice[0].array_iva[0].document_code == 5
        assert electronic_invoice[0].array_iva[0].amount == 210
        assert electronic_invoice[0].array_iva[0].taxable_base == 1000

        assert not (electronic_invoice[0].service_from and electronic_invoice[0].service_to)
        assert electronic_invoice[0].customer_document_type == '80'

    def test_electronic_invoice_details_nc_b(self):

        document_type_id = self.document_book_nc_b.document_type_id.id
        voucher_type = self.env['afip.voucher.type'].search([
            ('document_type_id', '=', document_type_id),
            ('denomination_id', '=', self.refund.denomination_id.id)],
            limit=1
        )
        document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))

        assert document_afip_code == 8
        electronic_invoice = self.refund._set_electronic_invoice_details(document_afip_code)

        # Validamos los montos
        assert electronic_invoice[0].taxed_amount == 2500
        assert electronic_invoice[0].untaxed_amount == 150
        assert electronic_invoice[0].exempt_amount == 0

        # Validamos el array de impuestos (deberia haber 1 iva del 10.5%)
        assert electronic_invoice[0].array_iva[0].document_code == 4
        assert electronic_invoice[0].array_iva[0].amount == 262.50
        assert electronic_invoice[0].array_iva[0].taxable_base == 2500

        assert (electronic_invoice[0].service_from and electronic_invoice[0].service_to)
        assert electronic_invoice[0].customer_document_type == '96'

    def test_electronic_invoice_details_nd_c(self):

        # Primero cambiamos al partner de la empresa a monotributista para que pueda realizar un documento tipo C
        mon = self.env.ref('l10n_ar_afip_tables.account_fiscal_position_mon')
        self.env.user.company_id.partner_id.property_account_position_id = mon.id
        self.debit_note.onchange_partner_id()
        document_type_id = self.document_book_nd_c.document_type_id.id
        voucher_type = self.env['afip.voucher.type'].search([
            ('document_type_id', '=', document_type_id),
            ('denomination_id', '=', self.debit_note.denomination_id.id)],
            limit=1
        )
        document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))
        assert document_afip_code == 12
        electronic_invoice = self.debit_note._set_electronic_invoice_details(document_afip_code)

        # Validamos los montos
        assert electronic_invoice[0].taxed_amount == 0
        assert electronic_invoice[0].untaxed_amount == 0
        assert electronic_invoice[0].exempt_amount == 0

        # Validamos el array de impuestos (deberia haber 1 iva Exento)
        assert electronic_invoice[0].array_iva[0].document_code == 2
        assert electronic_invoice[0].array_iva[0].amount == 0.0
        assert electronic_invoice[0].array_iva[0].taxable_base == 5000

        assert not (electronic_invoice[0].service_from and electronic_invoice[0].service_to)
        assert electronic_invoice[0].customer_document_type == '86'

    def test_electronic_invoice_details_perceptions(self):

        document_type_id = self.document_book_fc_a.document_type_id.id
        voucher_type = self.env['afip.voucher.type'].search([
            ('document_type_id', '=', document_type_id),
            ('denomination_id', '=', self.invoice.denomination_id.id)],
            limit=1
        )
        document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))
        self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iibb_pba_efectuada').id,
            'invoice_id': self.invoice.id,
            'amount': 10,
            'base': 1000,
            'jurisdiction': 'provincial',
            'name': 'percepcion pba'
        })
        self.invoice.onchange_perception_ids()
        electronic_invoice = self.invoice._set_electronic_invoice_details(document_afip_code)

        # Validamos los montos
        assert electronic_invoice[0].taxed_amount == 1000
        assert electronic_invoice[0].untaxed_amount == 0
        assert electronic_invoice[0].exempt_amount == 0

        # Validamos el array de impuestos (deberia haber 1 percepcion)
        assert electronic_invoice[0].array_tributes[0].document_code == 2
        assert electronic_invoice[0].array_tributes[0].amount == 10
        assert electronic_invoice[0].array_tributes[0].taxable_base == 1000
        assert electronic_invoice[0].array_tributes[0].aliquot == 0.01

    def test_electronic_invoice_multiple_perceptions_and_taxes(self):
        document_type_id = self.document_book_fc_a.document_type_id.id
        voucher_type = self.env['afip.voucher.type'].search([
            ('document_type_id', '=', document_type_id),
            ('denomination_id', '=', self.invoice.denomination_id.id)],
            limit=1
        )
        document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))

        # Creamos otro producto del 21
        invoice_line = self.env['account.invoice.line'].create({
            'name': 'product_21_test',
            'product_id': self.product_21_consu.id,
            'price_unit': 500,
            'account_id': self.product_21_consu.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.invoice.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 500

        # Creamos un producto del 10.5
        invoice_line = self.env['account.invoice.line'].create({
            'name': 'product_105_test',
            'product_id': self.product_105_serv.id,
            'price_unit': 500,
            'account_id': self.product_105_serv.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.invoice.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 500

        # Creamos una linea sin impuesto
        invoice_line = self.env['account.invoice.line'].create({
            'name': 'no_tax',
            'price_unit': 150,
            'account_id': self.product_105_serv.categ_id.property_account_income_categ_id.id,
            'invoice_id': self.invoice.id
        })
        invoice_line._onchange_product_id()
        invoice_line.price_unit = 150
        self.invoice._onchange_invoice_line_ids()

        # Asignamos percepciones
        self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iibb_pba_efectuada').id,
            'invoice_id': self.invoice.id,
            'amount': 20,
            'base': 2000,
            'jurisdiction': 'provincial',
            'name': 'percepcion pba'
        })
        self.env['account.invoice.perception'].create({
            'perception_id': self.env.ref('l10n_ar_perceptions.perception_perception_iva_efectuada').id,
            'invoice_id': self.invoice.id,
            'amount': 100,
            'base': 2000,
            'jurisdiction': 'nacional',
            'name': 'percepcion iva'
        })
        self.invoice.onchange_perception_ids()
        electronic_invoice = self.invoice._set_electronic_invoice_details(document_afip_code)

        # Validamos los montos
        assert electronic_invoice[0].taxed_amount == 2000
        assert electronic_invoice[0].untaxed_amount == 150
        assert electronic_invoice[0].exempt_amount == 0

        # Validamos el array de impuestos (deberia haber 1 iva del 10.5% y 1 del 21%)
        electronic_invoice[0].array_iva.sort(key=lambda x: x.document_code)
        assert electronic_invoice[0].array_iva[0].document_code == 4
        assert electronic_invoice[0].array_iva[0].amount == 52.5
        assert electronic_invoice[0].array_iva[0].taxable_base == 500
        assert electronic_invoice[0].array_iva[1].document_code == 5
        assert electronic_invoice[0].array_iva[1].amount == 315
        assert electronic_invoice[0].array_iva[1].taxable_base == 1500

        # Validamos el array de impuestos (deberia haber 2 percepciones, una nacional y una provincial)
        electronic_invoice[0].array_tributes.sort(key=lambda x: x.document_code)
        assert electronic_invoice[0].array_tributes[0].document_code == 1
        assert electronic_invoice[0].array_tributes[0].amount == 100
        assert electronic_invoice[0].array_tributes[0].taxable_base == 2000
        assert electronic_invoice[0].array_tributes[0].aliquot == 0.05
        assert electronic_invoice[0].array_tributes[1].document_code == 2
        assert electronic_invoice[0].array_tributes[1].amount == 20
        assert electronic_invoice[0].array_tributes[1].taxable_base == 2000
        assert electronic_invoice[0].array_tributes[1].aliquot == 0.01

    def test_tax_not_found(self):
        """ Si hay un impuesto que no es IVA y no se encuentra un percepcion asociada deberia tirar error """
        new_tax_group = self.env['account.tax.group'].create({
            'name': 'new_group'
        })
        self.invoice.tax_line_ids[0].tax_id.tax_group_id = new_tax_group.id
        with self.assertRaises(ValidationError):
            self.invoice._add_perceptions_to_electronic_invoice(mock.Mock())

    def test_write_wsfe_response(self):

        response = mock.Mock()
        invoice_detail = mock.Mock
        # Simulamos la respuesta de la AFIP
        response.FeCabResp.Resultado = 'A'
        response.FeCabResp.FchProceso = '20000101000000'

        self.invoice.write_wsfe_response(invoice_detail, response)

        # Nos aseguramos que en la base quede con el formato correspondiente
        assert self.invoice.wsfe_request_detail_ids[0].date == '2000-01-01 03:00:00'
        assert self.invoice.wsfe_request_detail_ids[0].result

    def test_wsfe_number(self):
        # Simulamos la respuesta de la AFIP y un numero distinto al siguiente del talonario
        afip_wsfe = mock.Mock()
        afip_wsfe.get_last_number = mock.MagicMock(return_value=1)

        with self.assertRaises(ValidationError):
            self.invoice._action_wsfe_number(self.document_book_fc_a, afip_wsfe, 001)

        # Ahora probamos el caso que coinciden ambos talonarios
        afip_wsfe.get_last_number = mock.MagicMock(return_value=0)
        self.invoice._action_wsfe_number(self.document_book_fc_a, afip_wsfe, 001)

    def test_get_wsfe(self):

        with self.assertRaises(ValidationError):
            self.invoice._get_wsfe()

        wsaa = self.env['wsaa.configuration'].create({
            'type': 'homologation',
            'name': 'wsaa',
            'private_key': config.private_key,
            'certificate': config.certificate
        })
        wsaa_token = self.env['wsaa.token'].create({
            'name': 'wsfe',
            'wsaa_configuration_id': wsaa.id,
        })
        self.env['wsfe.configuration'].create({
            'name': 'Test Wsfe',
            'type': 'homologation',
            'wsaa_configuration_id': wsaa.id,
            'wsaa_token_id': wsaa_token.id,
        })
        afip_wsfe = self.invoice._get_wsfe()

        assert afip_wsfe.__class__.__name__ == 'Wsfe'

    def test_set_invoice_details(self):
        assert not (self.invoice.date_service_from and self.invoice.date_service_to or self.invoice.afip_concept_id)
        self.invoice._set_empty_invoice_details()
        assert (self.invoice.date_service_from and self.invoice.date_service_to or self.invoice.afip_concept_id)

    def test_not_vat_in_partner(self):

        self.invoice.partner_id.partner_document_type_id = None

        # Sin tipo ni numero de documento
        with self.assertRaises(ValidationError):
            self.invoice._validate_required_electronic_fields()

        # Solo con numero
        self.invoice.partner_id.vat = '30709653543'
        with self.assertRaises(ValidationError):
            self.invoice._validate_required_electronic_fields()

        # Solo con tipo
        self.invoice.partner_id.partner_document_type_id = \
            self.env.ref('l10n_ar_afip_tables.partner_document_type_80').id
        self.invoice.partner_id.vat = None
        with self.assertRaises(ValidationError):
            self.invoice._validate_required_electronic_fields()

        # Con ambos
        self.invoice.partner_id.vat = '30709653543'
        self.invoice._validate_required_electronic_fields()

    def test_afip_concept_based_on_products(self):

        # 1 producto
        assert self.invoice._get_afip_concept_based_on_products().id == 1
        # 1 servicio
        assert self.refund._get_afip_concept_based_on_products().id == 2
        self.refund.invoice_line_ids[0].invoice_id = self.invoice.id
        # 1 producto y 1 servicio
        assert self.invoice._get_afip_concept_based_on_products().id == 3
        # Ningun producto ni servicio
        assert self.refund._get_afip_concept_based_on_products().id == 1

    def test_exists_commit(self):
        # Mockiamos el env para que el commit no commitee realmente en la base
        with mock.patch.object(self.invoice, 'env', return_value=True) as commitMock:
            self.invoice._commit()

    def test_action_electronic(self):
        """ Hacemos una simluacion de envio de factura a AFIP con Mocks """

        self.invoice.partner_id.partner_document_type_id =\
            self.env.ref('l10n_ar_afip_tables.partner_document_type_80').id
        self.invoice.partner_id.vat = '30709653543'

        get_wsfe = 'odoo.addons.l10n_ar_afip_webservices_wsfe.models.account_invoice.AccountInvoice._get_wsfe'
        commit = 'odoo.addons.l10n_ar_afip_webservices_wsfe.models.account_invoice.AccountInvoice._commit'
        # Mockiamos la funcion para simular el comportamiento de la afip
        with mock.patch(get_wsfe) as MockClass, mock.patch(commit) as commitMock:

            # Simulamos la respuesta de la afip y el wsfe
            response = mock.Mock()
            wsfe_mock = mock.Mock()
            response.FeCabResp.Resultado = 'A'
            response.FeCabResp.FchProceso = '20000101000000'
            response.FeDetResp.FECAEDetResponse = [mock.Mock()]
            response.FeDetResp.FECAEDetResponse[0].CAE = '123871298371923'
            response.FeDetResp.FECAEDetResponse[0].CAEFchVto = '20000110'

            # Simulamos las funciones del wsfe
            wsfe_mock.get_last_number = mock.MagicMock(return_value=0)
            wsfe_mock.get_cae = mock.MagicMock(return_value=response)
            MockClass.return_value = wsfe_mock
            commitMock.return_value = None

            # Enviamos la factura
            self.invoice.action_electronic(self.document_book_fc_a)
            assert self.invoice.cae == '123871298371923'
            assert self.invoice.cae_due_date == '2000-01-10'
            assert self.invoice.name == self.document_book_fc_a.pos_ar_id.name_get()[0][1]+'-'+'1'.zfill(8)

            # Como ya tiene cae no se deberia volver a enviar por lo que deberia tener el mismo numero
            self.invoice.action_electronic(self.document_book_fc_a)
            assert self.invoice.name == self.document_book_fc_a.pos_ar_id.name_get()[0][1]+'-'+'1'.zfill(8)

            # Probamos una factura rechazada
            self.invoice.cae = None
            wsfe_mock.get_last_number = mock.MagicMock(return_value=1)
            response.FeCabResp.Resultado = 'R'
            response.FeDetResp.FECAEDetResponse[0].Observaciones.Obs = [mock.Mock()]
            response.FeDetResp.FECAEDetResponse[0].Observaciones.Obs[0].Msg = 'Error XXX: Problema al validar la factura'
            with self.assertRaises(ValidationError):
                self.invoice.action_electronic(self.document_book_fc_a)

            # Probamos una factura con error en el momento de enviarse en afip
            wsfe_mock.get_cae = mock.Mock(side_effect=Exception("Error al enviar la factura"))
            with self.assertRaises(ValidationError):
                self.invoice.action_electronic(self.document_book_fc_a)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
