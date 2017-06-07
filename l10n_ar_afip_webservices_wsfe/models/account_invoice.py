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
from odoo_openpyme_api import documents
from openerp import models, fields
from odoo_openpyme_api.afip_webservices import wsfe, wsaa
from openerp.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    date_service_from = fields.Date('Fecha servicio inicial', help='Fecha inicial del servicio brindado')
    date_service_to = fields.Date('Fecha servicio final', help='Fecha final del servicio brindado')
    cae = fields.Char('Cae', readonly=True)
    afip_concept_id = fields.Many2one('afip.concept', 'Concepto')

    def action_electronic(self):
        """

        """
        afip_wsfe = self._get_wsfe()

        for invoice in self:

            # Validamos los campos
            invoice._validate_required_electronic_fields()

            # Obtenemos el codigo de comprobante
            document_type_id = invoice.get_document_book().document_type_id.id
            document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', document_type_id))

            # Validamos la numeracion
            invoice._action_wsfe_number(afip_wsfe, document_afip_code)

            # Armamos la factura
            electronic_invoice = invoice._set_electronic_invoice_details(document_afip_code)

            # Chequeamos el status de los servidores y enviamos la factura a AFIP.
            try:
                afip_wsfe.check_webservice_status()
                response = afip_wsfe.get_cae(electronic_invoice, invoice.pos_ar_id.name)
            except Exception, e:
                raise ValidationError(e.message)

            if response.FeCabResp.Resultado == 'R':
                # Traemos el conjunto de errores
                errores = '\n'.join(obs.Msg for obs in response.FeDetResp.FECAEDetResponse[0].Observaciones.Obs)\
                    if hasattr(response.FeDetResp.FECAEDetResponse[0], 'Observaciones') else ''
                raise ValidationError('Hubo un error al intentar validar el documento\n{0}'.format(errores))

            _logger.info('RESPONSE %s', response)
            # Commitiamos para que no halla inconsistencia con la AFIP
            self.env.cr.commit()

    def _set_electronic_invoice_details(self, document_afip_code):
        """ Mapea los valores de ODOO al objeto ElectronicInvoice"""

        self._set_empty_invoice_details()
        codes_models_proxy = self.env['codes.models.relation']

        # Seteamos los campos generales de la factura
        electronic_invoice = wsfe.invoice.ElectronicInvoice(document_afip_code)
        electronic_invoice.taxed_amount = self.amount_to_tax
        electronic_invoice.untaxed_amount = self.amount_not_taxable
        electronic_invoice.exempt_amount = self.amount_exempt
        electronic_invoice.document_date = datetime.strptime(
            self.date_invoice or fields.Date.context_today(self),
            '%Y-%m-%d'
        )
        if codes_models_proxy.get_code('afip.concept', self.afip_concept_id.id) in ['2', '3']:
            electronic_invoice.service_from = datetime.strptime(self.date_service_from, '%Y-%m-%d')
            electronic_invoice.service_to = datetime.strptime(self.date_service_to, '%Y-%m-%d')
        electronic_invoice.payment_due_date = datetime.strptime(
            self.date_due or fields.Date.context_today(self),
            '%Y-%m-%d'
        )
        electronic_invoice.customer_document_number = self.partner_id.vat
        electronic_invoice.customer_document_type = codes_models_proxy.get_code(
            'partner.document.type',
            self.partner_id.partner_document_type_id.id
        )
        # TODO: CAMBIAR DESPUES DE IMPORTAR MONEDAS
        electronic_invoice.mon_id = 'PES'
        electronic_invoice.mon_cotiz = self.currency_id.compute(1, self.company_id.currency_id)
        electronic_invoice.concept = int(codes_models_proxy.get_code(
            'afip.concept',
            self.afip_concept_id.id
        ))
        # Agregamos impuestos y percepciones
        self._add_vat_to_electronic_invoice(electronic_invoice)
        self._add_perceptions_to_electronic_invoice(electronic_invoice)
        return [electronic_invoice]

    def _add_vat_to_electronic_invoice(self, electronic_invoice):
        """ Agrega los impuestos que son iva a informar """

        group_vat = self.env.ref('l10n_ar.tax_group_vat')
        codes_models_proxy = self.env['codes.models.relation']
        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id == group_vat:
                code = int(codes_models_proxy.get_code('account.tax', tax.tax_id.id))
                electronic_invoice.add_iva(documents.tax.Iva(code, tax.amount, tax.base))

    def _add_perceptions_to_electronic_invoice(self, electronic_invoice):
        """ Agrega los impuestos que son percepciones """

        group_vat = self.env.ref('l10n_ar.tax_group_vat')
        codes_models_proxy = self.env['codes.models.relation']
        perception_perception_proxy = self.env['perception.perception']

        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id != group_vat:
                perception = perception_perception_proxy.search([('tax_id', '=', tax.tax_id.id)], limit=1)

                if not perception:
                    raise ValidationError("Percepcion no encontrada para el impuesto %s", tax.tax_id.name)

                code = int(codes_models_proxy.get_code('perception.perception', perception.id))
                tribute_aliquot = round(tax.amount / tax.base if tax.base else 0, 2)
                electronic_invoice.add_tribute(documents.tax.Tribute(code, tax.amount, tax.base, tribute_aliquot))

    def _action_wsfe_number(self, afip_wsfe, document_afip_code):
        """
        Valida que el ultimo numero del talonario sea el correcto en comparacion con el de la AFIP.
        :param afip_wsfe: instancia Wsfe.
        :param document_afip_code: Codigo de afip del documento.
        """

        last_number = str(afip_wsfe.get_last_number(self.pos_ar_id.name, document_afip_code) + 1)
        _logger.info('ULTIMO NUMERO? %s', last_number)
        _logger.info('ULTIMO NUMERO ODOO? %s', self.get_document_book().name)

        if last_number.zfill(8) != self.get_document_book().name.zfill(8):
            raise ValidationError('El ultimo numero del talonario no coincide con el de la afip')


    def _get_wsfe(self):
        """
        Crea el objeto de wsfe para utilizar sus servicios
        :return: instancia de Wsfe
        """
        wsfe_config = self.env['wsfe.configuration'].search([
            ('wsaa_token_id.name', '=', 'wsfe')
        ])

        if not wsfe_config:
            raise ValidationError('No se encontro una configuracion de factura electronica')

        access_token = self._get_access_token(wsfe_config)
        homologation = False if wsfe_config.type == 'production' else True
        afip_wsfe = wsfe.wsfe.Wsfe(access_token, self.company_id.vat, homologation)

        return afip_wsfe

    def _set_empty_invoice_details(self):
        """ Completa los campos de la invoice no establecidos a un default """

        vals = {}

        if not self.date_service_from:
            vals['date_service_from'] = datetime.now().strftime('%Y-%m-%d')
        if not self.date_service_to:
            vals['date_service_to'] = datetime.now().strftime('%Y-%m-%d')
        if not self.afip_concept_id:
            vals['afip_concept_id'] = self._get_afip_concept_based_on_products().id

        self.write(vals)

    def _validate_required_electronic_fields(self):
        if not (self.partner_id.vat and self.partner_id.partner_document_type_id):
            raise ValidationError('Por favor, configurar tipo y numero de documento en el cliente')

    def _get_afip_concept_based_on_products(self):
        """
        Devuelve el concepto de la factura en base a los tipos de productos
        :return: afip.concept, tipo de concepto
        """
        product_types = self.invoice_line_ids.mapped('product_id.type')

        # Estaria bueno pensar una forma para no hardcodearlo, ponerle el concepto en el producto
        # me parecio mucha configuracion a la hora de importar datos o para el cliente, quizas hacer un
        # compute?

        if len(product_types) > 1 and 'service' in product_types:
            # Productos y servicios
            code = '3'
        else:
            if 'service' in product_types:
                # Servicio
                code = '2'
            else:
                # Producto
                code = '1'

        return self.env['codes.models.relation'].get_record_from_code('afip.concept', code)


    @staticmethod
    def _get_access_token(wsfe_config):
        """
        Crea el objeto de ticket de acceso para utilizar en el wsfe
        :return: instancia de AcessToken
        """

        token = wsfe_config.wsaa_token_id
        token.action_renew()
        access_token = wsaa.tokens.AccessToken()
        access_token.sign = token.sign
        access_token.token = token.token

        return access_token

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
