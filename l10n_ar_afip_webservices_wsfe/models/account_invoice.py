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

import pytz
from collections import defaultdict
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from l10n_ar_api import documents
from l10n_ar_api.afip_webservices import wsfe
from openerp import models, fields, api, registry
from openerp.exceptions import ValidationError

MAX_LENGTH = 199


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    date_service_from = fields.Date('Fecha servicio inicial', help='Fecha inicial del servicio brindado')
    date_service_to = fields.Date('Fecha servicio final', help='Fecha final del servicio brindado')
    cae = fields.Char('CAE', readonly=True, copy=False)
    cae_due_date = fields.Date('Vencimiento CAE', readonly=True, copy=False)
    afip_concept_id = fields.Many2one('afip.concept', 'Concepto')
    wsfe_request_detail_ids = fields.Many2many(
        'wsfe.request.detail',
        'invoice_request_details',
        'invoice_id',
        'request_detail_id',
        string='Detalles Wsfe'
    )

    @api.multi
    def action_move_create(self):
        """
        En el modulo de PoS, se ejecuta la funcion del tipo de talonario una vez para cada factura. Aca busco que, si
        todas las facturas seleccionadas son electronicas, lo ejecute una sola vez con todas esas, haciendo los chequeos
        correspondientes
        :return: finalmente llama al super
        """
        invoices_by_document_book = defaultdict(list)
        all_invoices = self.browse(self.env.context.get('active_ids') or self.ids)
        invoice_types = all_invoices.mapped('type')

        for invoice in all_invoices:
            if not invoice.amount_total_signed:
                raise ValidationError("Ha seleccionado una o mas facturas con monto nulo")
            book = invoice.get_document_book()
            if book.book_type_id.type == 'electronic' and not invoice.cae:
                invoices_by_document_book[book].append(invoice.id)
            invoice._validate_fiscal_position_and_denomination()

        if (invoice_types == ['out_invoice'] or invoice_types == ['out_refund']) and invoices_by_document_book:
            afip_wsfe = all_invoices[0]._get_wsfe()
            for k, v in invoices_by_document_book.iteritems():
                # Obtenemos el codigo de comprobante
                document_type_id = k.document_type_id.id
                voucher_type = self.env['afip.voucher.type'].search([
                    ('document_type_id', '=', document_type_id),
                    ('denomination_id', '=', k.denomination_id.id)],
                    limit=1
                )
                document_afip_code = int(
                    self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))

                # Validamos la numeracion
                k.action_wsfe_number(afip_wsfe, document_afip_code)

            for k, v in invoices_by_document_book.iteritems():
                split_ids = [v[i:i + MAX_LENGTH] for i in range(0, len(v), MAX_LENGTH)]
                for split_list in split_ids:
                    invoices = self.browse(split_list)
                    getattr(invoices, k.book_type_id.foo)(k)
                    for invoice in invoices:
                        invoice.check_invoice_duplicity()
        return super(AccountInvoice, self).action_move_create()

    def action_electronic(self, document_book):
        """
        Realiza el envio a AFIP de la factura y escribe en la misma el CAE y su fecha de vencimiento.
        :raises ValidationError: Si el talonario configurado no tiene la misma numeracion que en AFIP.
                                 Si hubo algun error devuelto por afip al momento de enviar los datos.
        """
        electronic_invoices = []
        pos = document_book.pos_ar_id
        invoices = self.filtered(lambda l: not l.cae and l.amount_total and l.pos_ar_id == pos).sorted(lambda l: l.id)
        if invoices:
            afip_wsfe = invoices[0]._get_wsfe()

        for invoice in invoices:
            # Validamos los campos
            invoice._validate_required_electronic_fields()

            # Obtenemos el codigo de comprobante
            document_type_id = document_book.document_type_id.id
            voucher_type = self.env['afip.voucher.type'].search([
                ('document_type_id', '=', document_type_id),
                ('denomination_id', '=', invoice.denomination_id.id)],
                limit=1
            )
            document_afip_code = int(self.env['codes.models.relation'].get_code('afip.voucher.type', voucher_type.id))

            # Armamos la factura
            electronic_invoices.append(invoice._set_electronic_invoice_details(document_afip_code))

        if electronic_invoices:
            response = None
            new_cr = None

            # Chequeamos la conexion y enviamos las facturas a AFIP, guardando el JSON enviado, el response y mostrando
            # los errores (en caso de que los haya)
            try:
                afip_wsfe.check_webservice_status()
                response, invoice_detail = afip_wsfe.get_cae(electronic_invoices, pos.name)
                afip_wsfe.show_error(response)
            except Exception, e:
                new_cr = registry(self.env.cr.dbname).cursor()
                self.env.cr.rollback()
                raise ValidationError(e.message)
            finally:
                # Commiteamos para que no haya inconsistencia con la AFIP. Como ya tenemos el CAE escrito en la factura,
                # al validarla nuevamente no se vuelve a enviar y se va a mantener la numeracion correctamente
                if response and response.FeDetResp:
                    with api.Environment.manage():
                        cr_to_use = new_cr or self.env.cr
                        new_env = api.Environment(cr_to_use, self.env.uid, self.env.context)
                        invoices.write_wsfe_response(new_env, invoice_detail, response)
                        new_invoices = new_env['account.invoice'].browse(invoices.ids)
                        for invoice in new_invoices:
                            # Busco, dentro del detalle de la respuesta, el segmento correspondiente a la factura
                            number = document_book.next_number()
                            filt = filter(lambda l: l.CbteDesde == long(number[-8:]),
                                          response.FeDetResp.FECAEDetResponse)
                            resp = filt[0] if filt else None
                            if resp and resp.Resultado == 'A':
                                invoice.write({
                                    'cae': resp.CAE,
                                    'cae_due_date': datetime.strptime(resp.CAEFchVto,
                                                                      '%Y%m%d') if resp.CAEFchVto else None,
                                    'name': number
                                })
                            # Si el envio no fue exitoso, se retrocede un numero en el talonario para compensar el
                            # aumento realizado al enviar la factura fallida
                            else:
                                document_book.prev_number()
                        self._commit(new_env)

            if response and response.FeCabResp and response.FeCabResp.Resultado == 'R':
                # Traemos el conjunto de errores
                errores = '\n'.join(obs.Msg for obs in response.FeDetResp.FECAEDetResponse[0].Observaciones.Obs) \
                    if hasattr(response.FeDetResp.FECAEDetResponse[0], 'Observaciones') else ''
                raise ValidationError('Hubo un error al intentar validar el documento\n{0}'.format(errores))

    def write_wsfe_response(self, env, invoice_detail, response):
        """ Escribe el envio y respuesta de un envio a AFIP """
        if response.FeCabResp:
            # Nos traemos el offset de la zona horaria para dejar en la base en UTC como corresponde
            offset = datetime.now(pytz.timezone('America/Argentina/Buenos_Aires')).utcoffset().total_seconds() / 3600
            fch_proceso = datetime.strptime(response.FeCabResp.FchProceso, '%Y%m%d%H%M%S') - relativedelta(hours=offset)
            result = response.FeCabResp.Resultado
            date = fch_proceso
        else:
            result = "Error"
            date = fields.Datetime.now()

        env['wsfe.request.detail'].sudo().create({
            'invoice_ids': [(4, self.ids)],
            'request_sent': invoice_detail,
            'request_received': response,
            'result': result,
            'date': date,
        })

    def _commit(self, env):
        env.cr.commit()

    @staticmethod
    def convert_currency(from_currency, to_currency, amount=1.0, d=None):
        """
        Convierte `amount` de `from_currency` a `to_currency` segun la cotizacion de la fecha `d`.
        :param from_currency: La moneda que queremos convertir.
        :param to_currency: La moneda a la que queremos convertir.
        :param amount: La cantidad que queremos convertir (1 para sacar el rate de la moneda).
        :param d: La fecha que se usara para tomar la cotizacion de ambas monedas.
        :return: El valor en la moneda convertida segun el rate de conversion.
        """
        if from_currency.id == to_currency.id:
            return amount
        if not d:
            d = str(date.today())
        from_currency_with_context = from_currency.with_context(date=d)
        to_currency_with_context = to_currency.with_context(date=d)
        converted_amount = from_currency_with_context.compute(
            amount, to_currency_with_context, round=False
        )
        return converted_amount

    def _set_electronic_invoice_details(self, document_afip_code):
        """ Mapea los valores de ODOO al objeto ElectronicInvoice"""

        self._set_empty_invoice_details()
        denomination_c = self.env.ref('l10n_ar_afip_tables.account_denomination_c')
        codes_models_proxy = self.env['codes.models.relation']

        # Seteamos los campos generales de la factura
        electronic_invoice = wsfe.invoice.ElectronicInvoice(document_afip_code)
        electronic_invoice.taxed_amount = self.amount_to_tax
        electronic_invoice.untaxed_amount = self.amount_not_taxable if self.denomination_id != denomination_c else 0
        electronic_invoice.exempt_amount = self.amount_exempt if self.denomination_id != denomination_c else 0
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
        electronic_invoice.mon_id = self.env['codes.models.relation'].get_code(
            'res.currency',
            self.currency_id.id
        )
        electronic_invoice.mon_cotiz = self.convert_currency(
            from_currency=self.currency_id,
            to_currency=self.company_id.currency_id,
            d=self.date_invoice
        )

        electronic_invoice.concept = int(codes_models_proxy.get_code(
            'afip.concept',
            self.afip_concept_id.id
        ))
        # Agregamos impuestos y percepciones
        self._add_vat_to_electronic_invoice(electronic_invoice)
        self._add_perceptions_to_electronic_invoice(electronic_invoice)
        return electronic_invoice

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
        perception_perception_proxy = self.env['perception.perception']

        for tax in self.tax_line_ids:
            if tax.tax_id.tax_group_id != group_vat:
                perception = perception_perception_proxy.search([('tax_id', '=', tax.tax_id.id)], limit=1)

                if not perception:
                    raise ValidationError("Percepcion no encontrada para el impuesto %s" + tax.tax_id.name)

                code = perception.get_afip_code()
                tribute_aliquot = round(tax.amount / tax.base if tax.base else 0, 2)
                electronic_invoice.add_tribute(documents.tax.Tribute(code, tax.amount, tax.base, tribute_aliquot))

    def _get_wsfe(self):
        """
        Busca el objeto de wsfe para utilizar sus servicios
        :return: instancia de Wsfe
        """
        wsfe_config = self.env['wsfe.configuration'].search([
            ('wsaa_token_id.name', '=', 'wsfe')
        ])

        if not wsfe_config:
            raise ValidationError('No se encontro una configuracion de factura electronica')

        access_token = wsfe_config.wsaa_token_id.get_access_token()
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
