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

from openerp import models, fields, api
from openerp.exceptions import Warning
import logging
_logger = logging.getLogger(__name__)


class ComputeRetentionWizard(models.TransientModel):

    _name = "compute.retention.wizard"

    @api.onchange('compute_retention_invoice_ids')
    def onchange_compute_retention_invoice_ids(self):

        amount = 0

        for document in self.compute_retention_invoice_ids:

            if document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed > 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    amount -= document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed)

                else:

                    amount += document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed)

            elif document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed == 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    amount -= document.amount

                else:

                    amount += document.amount

        self.account_invoice_ids = None
        self.withholding_amount = amount


    @api.multi
    def create_documents_to_concile(self):

        company_currency = self.env['res.users'].browse(self.env.uid).company_id.currency_id
        voucher = self.env['account.voucher'].browse(self.env.context.get('active_id'))
        journal_currency = voucher.journal_id.currency if voucher.journal_id.currency else company_currency
        if journal_currency is not company_currency:
            
            raise Warning ('No se pueden calcular retenciones para un diario con moneda distinta al de la compania')    
                    
                    
        if self._check_m_invoices() and self._check_wh_amount() >= 1000:
           
            voucher.retention_ids.unlink()
            self._create_m_retentions()
            
        else:
                
            compute_retention_invoice_proxy = self.env['compute.retention.invoice']
            retention_invoice_ids = []
            withholding_amount = 0.0
            actual_retention = 0.0

            for invoice in sorted(self.account_invoice_ids, key=lambda x: x.type_analysis):
    
                move_line_currency = self.env['account.move.line'].search([('move_id', '=', invoice.move_id.id), ('account_id', '=', invoice.account_id.id)])
           
                cotization = 1
                if move_line_currency:
                    
                    move_line = move_line_currency[0]
                    if move_line.amount_currency:
                        
                        price = move_line.credit if move_line.credit else move_line.debit
                        
                        cotization = abs(price / move_line.amount_currency)
                        
                last_retention = actual_retention
    
                #~ BUGFIX PARA LOS ONCHANGE DE MANY2MANY, AGREGA LOG PARA CARGAR CACHE
                _logger.info('PARAM INV: BALANCE %s, TOTAL %s, NETO GRAVADO %s',invoice.residual, invoice.amount_total, invoice.amount_taxed)
                if invoice.amount_total > 0 and invoice.amount_taxed > 0 and invoice.residual > 0:
    
                    if invoice.type == 'in_refund':
    
                        withholding_amount -= cotization * (invoice.residual /  ( invoice.amount_total / invoice.amount_taxed))
    
                    else:
    
                        withholding_amount += cotization * (invoice.residual /  ( invoice.amount_total / invoice.amount_taxed))
    
                elif invoice.amount_total > 0 and invoice.amount_taxed == 0 and invoice.residual > 0:
    
                    if invoice.type == 'in_refund':
    
                        withholding_amount -= cotization * (invoice.amount_total)
    
                    else:
    
                        withholding_amount += cotization * (invoice.amount_total)
    
                actual_retention = self.with_context(document_amount=withholding_amount).action_compute()[0]
                amount_of_retentions =  actual_retention - last_retention
                                
                compute_retention_invoice = compute_retention_invoice_proxy.create({
                    'invoice_id': invoice.id,
                    'amount': invoice.residual,
                    'amount_of_retentions': amount_of_retentions,
                    'amount_to_pay': invoice.residual - amount_of_retentions/cotization if amount_of_retentions >= 0 else -(invoice.residual/cotization + amount_of_retentions),
                    'currency_id': invoice.currency_id.id,
                    'cotization': cotization})
    
                retention_invoice_ids.append(compute_retention_invoice.id)
    
            if retention_invoice_ids:
    
                self.compute_retention_invoice_ids = [(6, 0, retention_invoice_ids)]
    
            self.withholding_amount = withholding_amount
            self.valid = True

            return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'compute.retention.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
            }


    ''' Recalcula las retenciones en caso que se modifiquen los importes
    '''
    @api.multi
    def recalculate_documents(self):

        withholding_amount = 0.0
        actual_retention = 0.0

        for retention_invoice in self.compute_retention_invoice_ids:

            last_retention = actual_retention

            #~ BUGFIX PARA LOS ONCHANGE DE MANY2MANY, AGREGA LOG PARA CARGAR CACHE
            _logger.info('PARAM INV: BALANCE %s, TOTAL %s, NETO GRAVADO %s', retention_invoice.invoice_id.residual, \
                         retention_invoice.invoice_id.amount_total, retention_invoice.invoice_id.amount_taxed)

            if retention_invoice.invoice_id.amount_total > 0 and \
            retention_invoice.invoice_id.amount_taxed > 0 and retention_invoice.amount > 0:

                if retention_invoice.invoice_id.type == 'in_refund':

                    withholding_amount -= retention_invoice.amount * retention_invoice.cotization/ \
                        ( retention_invoice.invoice_id.amount_total / retention_invoice.invoice_id.amount_taxed)

                else:

                    withholding_amount += retention_invoice.amount * retention_invoice.cotization/ \
                        ( retention_invoice.invoice_id.amount_total / retention_invoice.invoice_id.amount_taxed)

            actual_retention = self.with_context(document_amount=withholding_amount).action_compute()[0]
            amount_of_retentions =  actual_retention - last_retention
            retention_invoice.amount_of_retentions = amount_of_retentions

        self.retention_advance_amount = self.with_context(document_amount=withholding_amount+self.advance_amount).action_compute()[0] - actual_retention
        self.withholding_amount = withholding_amount + self.advance_amount

        return {
                'context': self.env.context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'compute.retention.wizard',
                'res_id': self.id,
                'view_id': False,
                'type': 'ir.actions.act_window',
                'target': 'new',
          }


    ''' Buscamos las facturas pertenecientes al proveedor
    '''
    def _get_invoice_domain(self):

        #Como se ejecuta el domain en la creación del wizard todavía no tenemos el partner, lo traemos por active_id
        partner_id = self.env['account.voucher'].browse(self.env.context.get('active_id')).partner_id.id

        invoice_list = self.env['account.invoice'].search([
            '|',
            ('type', '=', 'in_refund'),
            ('type', '=', 'in_invoice'),
            ('partner_id','=', partner_id),
            ('state','=','open')
        ]).ids

        return [('id','in',invoice_list)]

    partner_id = fields.Many2one('res.partner', string="Partner")
    valid = fields.Boolean('Validado')
    account_invoice_id = fields.Many2one('account.invoice', string="Facturas")
    account_invoice_ids = fields.Many2many('account.invoice', 'update_retention_wizard_rel', 'update_retention_wizard_id',
                                           'invoice_id', string="Documentos", domain=_get_invoice_domain)
    advance_amount = fields.Float('Importe a cuenta')
    retention_advance_amount = fields.Float('Retencion de importe a cuenta')
    withholding_amount = fields.Float(string="Importe documentos")
    #Como los documentos los creamos nosotros desde un on changue, al no poder eliminar el "Añadir un elemento", filtramos
    #el dominio para que no halla manera que se pueda agregar ningun documento mas que los creados desde el onchangue.
    compute_retention_invoice_ids = fields.Many2many('compute.retention.invoice', 'compute_retention_invoice_wizard_rel',
                                                     string="Documentos", domain="[('id', '=', None)]")
    
    
    def change_valid (self):

        self.valid = True

    def _set_withholding_amount(self):

        withholding_amount = 0.0

        for document in self.compute_retention_invoice_ids:

            if document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed > 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    withholding_amount -= document.cotization * (document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed))

                else:

                    withholding_amount += document.cotization * (document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed))

            elif document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed == 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    withholding_amount -= document.cotization * document.amount

                else:

                    withholding_amount += document.cotization * document.amount


        self.withholding_amount = withholding_amount + self.advance_amount

        return self.withholding_amount

    ''' Devuelve el valor del withholding amount desde las lineas. Usado para verificar si corresponde
    Con el usado para calcular las retenciones.
    '''
    def _check_withholding_amount(self):

        withholding_amount = 0.0

        for document in self.compute_retention_invoice_ids:

            if document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed > 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    withholding_amount -= document.cotization * (document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed))

                else:

                    withholding_amount += document.cotization * (document.amount /  ( document.invoice_id.amount_total / document.invoice_id.amount_taxed))

            elif document.invoice_id.amount_total > 0 and document.invoice_id.amount_taxed == 0 and document.invoice_id.residual > 0:

                if document.invoice_id.type == 'in_refund':

                    withholding_amount -= document.cotization * document.amount

                else:

                    withholding_amount += document.cotization * document.amount


        withholding_amount += self.advance_amount

        return withholding_amount

    #Verifica si estan en un rango corto los numeros para validaciones
    def isclose(self, a, b, rel_tol=1e-09, abs_tol=0.0):

        return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

    @api.one
    def action_compute(self):

        active_ids = self.env.context['active_ids']

        if not 'document_amount' in self.env.context.keys():

            if not self.isclose(self._check_withholding_amount(), self.withholding_amount):

                raise Warning('Por favor, seleccionar en el botón "Recalcular"')

        self._set_withholding_amount()

        if len(active_ids) != 1:
            raise Warning('El calculo se deberia realizar solo sobre un comprobante.')

        voucher = self.env['account.voucher'].browse(active_ids)

        if not voucher.company_id:
            raise Warning('El recibo debe tener una empresa configurada.')


        #~ ELIMINO RETENCIONES CARGADAS EN EL VOUCHER.
        if not 'document_amount' in self.env.context.keys():

            voucher.retention_ids.unlink()

        total_retentions = 0.0
        acumulated = 0.0

        #~ ITERO POR LAS REGLAS DE RETENCIONES DE LA EMPRESA
        #~ rcr --> RES COMPANY RETENTIONS
        for rcr in voucher.company_id.retention_ids:

            if not rcr.retention_id.retention_rule_ids:
                raise Warning ('Cuidado! Para esta retencion se debe configurar una regla: ', rcr.retention_id.name)

            #~ BUSCO SI EL PARTNER A RETENER TIENE UNA REGLA PARA ESTA RETENCION
            retention_partner = voucher.partner_id.retention_partner_rule_ids.filtered(lambda r: r.retention_id.id == rcr.retention_id.id)

            #FUNCION PARA CALCULO DE IIBB
            def gross_income_compute():

                base = self.withholding_amount if not 'document_amount' in self.env.context.keys() else self.env.context.get('document_amount')
                rule = rcr.retention_id.retention_rule_ids[0]

                #~ SI EL CLIENTE TIENE REGLA PISO EL PORCENTAJE
                percentage = retention_partner.percentage if retention_partner else rule.percentage

                if base <= rule.minimun_no_aplicable:

                    ret_amount = 0

                elif rule.exclude_minimun:

                    ret_amount = percentage / 100 * (base - rule.minimun_no_aplicable)

                    ret_amount = 0 if ret_amount < rule.minimun_tax else ret_amount

                else:

                    ret_amount = percentage / 100 * (base)

                    ret_amount = 0 if ret_amount < rule.minimun_tax else ret_amount

                res = {

                    'base': base,
                    'amount': ret_amount,
                    'regimen': False,
                    'regimen_code': False,
                    'activity_id': False,

                }

                return res

            #FUNCION PARA CALCULO DE IVA
            def vat_compute():

                raise Warning('El aplicativo no realiza calculo automatico para retenciones de iva.')

            #FUNCION PARA CALCULO DE GANANCIAS
            def profit_compute():

                #~ SI EL CLIENTE NO TIENE REGLA DEVUELVE ERROR.
                if not retention_partner:
                    raise Warning('Para el calculo de retenciones de ganancias el partner debe tener una regla de retencion configurada.')

                rule = retention_partner.retention_id.retention_rule_ids.filtered(lambda r: r.activity_id.id == retention_partner.activity_id.id)

                if not rule:
                    raise Warning('Algun error de configuracion en las reglas de retencion o partner')

                amount = self.withholding_amount if not 'document_amount' in self.env.context.keys() else self.env.context.get('document_amount')
                minimo = rule.minimun_no_aplicable
                percentage = rule.percentage

                minimo_ret = (percentage / 100) * minimo
                acum_ret = 0
                acum_ret -= minimo_ret
                acum = amount

                prev_vouchers = self.env['account.voucher'].search([
                    ('partner_id','=',voucher.partner_id.id),
                    ('period_id','=',voucher.period_id.id),
                    ('state','=', 'posted'),
                    ('type', '=', 'payment')
                ])

                prev_vouchers_sorted = prev_vouchers.sorted(key=lambda r: (r.date, r.id))

                for prev_voucher in prev_vouchers_sorted:

                    prev_voucher_acumulated = self._get_profit_retention(prev_voucher)
                    acum += prev_voucher_acumulated
                    acum_ret += prev_voucher_acumulated * (percentage / 100)
                    _logger.info('acum %s, acum_ret %s, prev_voucher N %s', acum, acum_ret, prev_voucher.reference)

                if acum <= rule.minimun_no_aplicable:
                    ret_amount = 0

                elif rule.exclude_minimun:

                    if acum_ret < 0:

                        ret_amount = acum_ret + ((percentage / 100) * amount)

                    #En caso que la retención sea la primera del mes, si ya hubo importes menores al mínimo
                    #previamente se deben realizar en ésta retención.
                    elif (acum_ret < rule.minimun_tax):

                        amount = acum - rule.minimun_no_aplicable
                        ret_amount = ((percentage/100) * acum) - minimo_ret

                    else:

                        ret_amount = ((percentage/100) * acum) - minimo_ret - acum_ret

                    if acum - amount < rule.minimun_no_aplicable:
                        amount = acum - rule.minimun_no_aplicable

                    if ret_amount < rule.minimun_tax:
                        ret_amount = 0

                else:
                    ret_amount = percentage / 100 * (acum)
                    ret_amount = ret_amount - acum_ret
                    if ret_amount < rule.minimun_tax:
                        ret_amount = 0


                res = {

                    'base': amount,
                    'amount': ret_amount,
                    'regimen': rule.activity_id.name,
                    'regimen_code': rule.activity_id.code,
                    'activity_id': rule.activity_id.id

                }

                return res

            #DELEGACION DE FUNCION SEGUN TIPO DE RETENTION
            options = {

                'gross_income' : gross_income_compute,
                'profit' : profit_compute,
                'vat' : vat_compute,

            }

            #USO DE FUNCION SEGUN TIPO DE RETENCION
  
            res = options[rcr.retention_id.type]()
            
            notes = ''
            if self.compute_retention_invoice_ids:
                notes += 'Retención según '
                for cr_invoice in self.compute_retention_invoice_ids:
                    note_pattern = '{tipo}{numero}, '
                    notes += note_pattern.format(
                        tipo=str(cr_invoice.type_analysis).upper(),
                        numero=cr_invoice.name,
                    ) 

            ret_tax_line_data = {

                'voucher_id': voucher.id,
                'date': voucher.date,
                'name': rcr.retention_id.name,
                'retention_id': rcr.retention_id.id,
                'tax_code_id': rcr.retention_id.tax_id.tax_code_id.id,
                'base_code_id': rcr.retention_id.tax_id.base_code_id.id,
                'account_id': rcr.retention_id.tax_id.account_collected_id.id,
                'state_id':  rcr.retention_id.state_id.id,
                'notes': notes,

            }

            ret_tax_line_data['regimen'] = res['regimen']
            ret_tax_line_data['regimen_code'] = res['regimen_code']
            ret_tax_line_data['base'] = res['base']
            ret_tax_line_data['amount'] = res['amount']
            ret_tax_line_data['activity_id'] = res['activity_id']

            if not 'document_amount' in self.env.context.keys():

                if ret_tax_line_data['amount'] > 0:

                    acumulated += res['amount']

                    if not self.env['retention.tax.line'].create( ret_tax_line_data ):
                        raise Warning('Ha ocurrido algun error al queres cargar la retencion:', rcr.retention_id.name)

            total_retentions += ret_tax_line_data['amount']

        voucher.amount += acumulated

        if not 'document_amount' in self.env.context.keys(): self.compute_lines()

        return total_retentions

    #~ FUNCION PARA BUSCAR LA RETENCION ACUMULADA

    def _get_profit_retention(self, prev_voucher):

        amount_debit = 0
        amount_credit = 0
        acum = 0
        retentions = 0

        vouchers_amount = self._get_vouchers(prev_voucher)

        for retention in prev_voucher.retention_ids:

            retentions += retention.amount

        _logger.info('Total de retenciones para el pago %s', retentions)

        for invoice in prev_voucher.line_dr_ids:

            amount_debit += invoice.amount

            if invoice.move_line_id:

                invoice_tax = 1
                
                if invoice.move_line_id.invoice:
                    
                    if invoice.move_line_id.invoice.amount_total > 0 and invoice.move_line_id.invoice.amount_taxed > 0:
                        
                        invoice_tax = invoice.move_line_id.invoice.amount_total / invoice.move_line_id.invoice.amount_taxed

                if vouchers_amount:

                    if vouchers_amount <= invoice.amount:

                        acum += ((invoice.amount - vouchers_amount) / invoice_tax)
                        vouchers_amount = 0
                        _logger.info('Imputacion de debitos con sobrante')

                    elif vouchers_amount >= invoice.amount:

                        vouchers_amount -= invoice.amount
                        _logger.info('Imputacion de debitos')

                else:

                    acum += invoice.amount / invoice_tax
                
                _logger.info('Total debito %s', acum)

        for credit in prev_voucher.line_cr_ids:

            amount_credit += credit.amount

            if credit.move_line_id.invoice:

                invoice_tax = credit.move_line_id.invoice.amount_total / credit.move_line_id.invoice.amount_taxed
                acum -= credit.amount / invoice_tax

        _logger.info('Total con creditos %s', acum)

        writeoff = prev_voucher.amount - amount_debit + amount_credit
        acum += writeoff - retentions

        _logger.info('Pago a cuenta restante %s', writeoff)

        return acum

    def _get_vouchers(self, prev_voucher):

        total = 0

        for voucher in prev_voucher.line_cr_ids:

            if not voucher.move_line_id.invoice:

                total += voucher.amount

        return total


    @api.one
    def compute_lines(self):

        account_voucher_line_proxy = self.env['account.voucher.line']
        voucher = self.env['account.voucher'].browse(self.env.context.get('active_id'))

        #Borramos las lineas del voucher. Luego se traeran las que se necesiten con los importes correspondientes
        account_voucher_line_proxy.search([('voucher_id', '=', voucher.id)]).unlink()

        lines = voucher.onchange_partner_id(voucher.partner_id.id, voucher.journal_id.id, voucher.amount, voucher.currency_id.id, voucher.type, voucher.date)

        #Buscamos en el diccionario del onchangue que es el que crea las lineas en el voucher al seleccionar diario o partner
        #De ahi tomamos los datos para poder crearlas
        if 'line_cr_ids' in lines['value']:

            for line_cr in lines['value']['line_cr_ids']:

                line_cr['voucher_id'] = voucher.id
                account_voucher_line_proxy.create(line_cr)

        if 'line_dr_ids' in lines['value']:

            for line_dr in lines['value']['line_dr_ids']:

                line_dr['voucher_id'] = voucher.id
                account_voucher_line_proxy.create(line_dr)

        #TODO: En lugar de rehacer la busqueda, guardarlas de las previas iteraciones donde se crean
        line_ids = self.env['account.voucher.line'].search([('voucher_id', '=', voucher.id)])

        if self.compute_retention_invoice_ids:

            invoice_ids = self.compute_retention_invoice_ids.mapped('invoice_id.id')

            for line in line_ids:

                #TODO: Fijarse si esta forma es la correcta (sin traer pagos a cta)
                #if (not line.move_line_id.invoice) or (line.move_line_id.invoice.id not in invoice_ids):
                if line.move_line_id.invoice:

                    if (line.move_line_id.invoice.id not in invoice_ids):

                        line_ids = line_ids - line
                        line.unlink()

                    else:

                        retention_invoice = self.compute_retention_invoice_ids.filtered(lambda r: r.invoice_id == line.move_line_id.invoice)

                        if len(retention_invoice) == 1:

                            line.amount = retention_invoice.amount * retention_invoice.cotization if \
                                retention_invoice.cotization *  retention_invoice.amount  <= line.current_balance\
                                else line.current_balance

                        else:

                            raise Warning('Hubo un problema al imputar los importes de la retencion')


        voucher.manual_imputation = True;



    ''' ------------ RETENCIONES DE FACTURAS M ----------------- '''

    def _check_wh_amount(self):
        
        wh_amount = 0
        
        for invoice in self.account_invoice_ids:
            
            wh_amount += invoice.amount_untaxed if invoice.type == ('in_invoice') else -invoice.amount_untaxed
            
        return wh_amount
    
    def _create_m_retentions(self):
        
        retention_proxy = self.env['retention.retention']
        retention_activity_proxy = self.env['retention.activity']
        voucher_amount = 0
        active_ids = self.env.context['active_ids']
        voucher = self.env['account.voucher'].browse(active_ids)
                
        #Primero validamos que existan todas las retenciones y regimenes necesarios
        profit_retention = retention_proxy.search([
            ('type', '=', 'profit'),
            ('type_tax_use', '=', 'purchase'),
        ])
        
        iva_retention = retention_proxy.search([
            ('type', '=', 'vat'),
            ('type_tax_use', '=', 'purchase'),
        ])
        
        if profit_retention: profit_retention = profit_retention[0]
        else:
            raise Warning('No se encontró retencion de ganancias creada.\n\
                Por favor, crear una')
        
        if iva_retention: iva_retention = iva_retention[0]
        else:
            raise Warning('No se encontró retencion de iva creada.\n\
                Por favor, crear una')
                
        profit_activity = retention_activity_proxy.search([('code', '=', 99)])
        iva_activity = retention_activity_proxy.search([('code', '=', 499)])
        
        
        if profit_activity: profit_activity = profit_activity[0]
        else:
            raise Warning('No se encontró la actividad para Facura M - Ganancias\n\
                Codigo de regimen 99. Por favor, crearla.')
            
        if iva_activity: iva_activity = iva_activity[0]
        else:
            raise Warning('No se encontró la actividad para Facura M - IVA\n\
                Codigo de regimen 499. Por favor, crearla.')

        
        #Luego realizamos el calculo
        for invoice in self.account_invoice_ids:
            
            vat_amount = self._get_invoice_vat_amount(invoice)
            
            # 3% para ganancias  
            voucher_amount += self._create_m_retention_tax_line(invoice, profit_retention, invoice.amount_untaxed * 0.03, profit_activity)              
    
            # 100% del iva
            voucher_amount += self._create_m_retention_tax_line(invoice, iva_retention, vat_amount, iva_activity)  
            
            # Ingresos brutos standard
            voucher_amount += self._create_m_iibb_retention(invoice)
            
        voucher.amount = invoice.amount_total
            
    def _create_m_retention_tax_line(self, invoice, retention, amount, activity=None):
        
        active_ids = self.env.context['active_ids']
        voucher = self.env['account.voucher'].browse(active_ids)

        note_pattern = '{tipo}{numero}, '
        notes = note_pattern.format(
            tipo=str(invoice.type_analysis).upper(),
            numero=invoice.name,
        )             


        ret_tax_line_data = {

            'voucher_id': voucher.id,
            'date': voucher.date,
            'name': retention.name,
            'retention_id': retention.id,
            'tax_code_id': retention.tax_id.tax_code_id.id,
            'base_code_id': retention.tax_id.base_code_id.id,
            'account_id': retention.tax_id.account_collected_id.id,
            'state_id': retention.state_id.id,
            'notes': notes,

        }
                    
        ret_tax_line_data['regimen'] = activity.name if activity else False
        ret_tax_line_data['regimen_code'] = activity.code if activity else False
        ret_tax_line_data['activity_id'] = activity.id if activity else False 
        ret_tax_line_data['base'] = invoice.amount_untaxed
        ret_tax_line_data['amount'] = amount
        
        retention_tax_line = self.env['retention.tax.line'].create(ret_tax_line_data)
        
        return retention_tax_line.amount
 
    def _get_invoice_vat_amount(self, invoice):
        
        vat_amount = 0.0
        for tax_line in invoice.tax_line:
            
            if tax_line.tax_id.tax_group == 'vat':
                
                vat_amount += tax_line.amount
        
        return vat_amount
    
    def _create_m_iibb_retention(self, invoice):
        
        base = invoice.amount_untaxed
        active_ids = self.env.context['active_ids']
        voucher = self.env['account.voucher'].browse(active_ids)
                
        for rcr in voucher.company_id.retention_ids:
            
            if rcr.type in ('profit', 'vat'):
                continue
            
            retention_partner = voucher.partner_id.retention_partner_rule_ids.filtered(lambda r: r.retention_id.id == rcr.retention_id.id)

            rule = rcr.retention_id.retention_rule_ids[0]
    
            #~ SI EL CLIENTE TIENE REGLA PISO EL PORCENTAJE
            percentage = retention_partner.percentage if retention_partner else rule.percentage
    
            if base <= rule.minimun_no_aplicable:
    
                ret_amount = 0
    
            elif rule.exclude_minimun:
    
                ret_amount = percentage / 100 * (base - rule.minimun_no_aplicable)
    
                ret_amount = 0 if ret_amount < rule.minimun_tax else ret_amount
    
            else:
    
                ret_amount = percentage / 100 * (base)
    
                ret_amount = 0 if ret_amount < rule.minimun_tax else ret_amount
    
            if ret_amount:
                
                self._create_m_retention_tax_line(invoice, rcr.retention_id, ret_amount)

            return ret_amount
        
    def _check_m_invoices(self):
        ''' Miramos si hay facturas M para retener. 
            Por el momento no se pueden mezclar con otras denominaciones '''
        
        den_list = []
        has_m_higer_than_1000 = False
         
        for invoice in self.account_invoice_ids:
            
            den_list.append(invoice.denomination_id.name)
            
            if invoice.denomination_id.name == 'M' and invoice.amount_untaxed >= 1000:    
               
                has_m_higer_than_1000 = True

        #Para el caso que halla varias facturas pero menores a 1000, se retiene normal
        if has_m_higer_than_1000:
            
            if len(den_list) > 1:
                
                raise Warning('Solo se pueden retener UNA factura M sin otras facturas en conjunto') 
                    
            return True
        
        return False
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
