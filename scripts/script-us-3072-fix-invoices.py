from datetime import datetime

import odoo
import json

DB_NAME = 'MAXTRACKER'
ODOO_CONF = '/etc/odoo/odoo.conf'
UID = odoo.SUPERUSER_ID

odoo.tools.config.parse_config(['--config=%s' % ODOO_CONF])
with odoo.api.Environment.manage():
    registry = odoo.modules.registry.RegistryManager.get(DB_NAME)
    with registry.cursor() as cr:
        ctx = odoo.api.Environment(cr, UID, {})['res.users'].context_get()
        env = odoo.api.Environment(cr, UID, ctx)
        invoice_proxy = env['account.invoice']
        partner_proxy = env['res.partner']
        invoices = invoice_proxy.search([('state', '=', 'draft'), ('date_due', '!=', False)])
        response = invoices[0].wsfe_request_detail_ids[0].request_received
        response = response.replace("'", '"').replace('False', 'false').replace('None', 'false').replace('L,', ',')
        dump = json.loads(r'{}'.format(response))
        det_resp = dump['FeDetResp']['FECAEDetResponse']
        for invoice in invoices:
            filt = filter(lambda l: l['DocNro'] == int(invoice.partner_id.vat), det_resp)
            resp = filt[0] if filt else None
            invoice.write({
                'cae': resp['CAE'],
                'cae_due_date': datetime.strptime(resp['CAEFchVto'], '%Y%m%d'),
                'name': invoice.pos_ar_id.name.zfill(4) + '-' + str(resp['CbteDesde']).zfill(8),
            })
