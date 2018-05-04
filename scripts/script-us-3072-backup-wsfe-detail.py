import pickle
from collections import defaultdict

import odoo

DB_NAME = 'QA_MAXTRACKER'
ODOO_CONF = '/etc/odoo/odoo.conf'
UID = odoo.SUPERUSER_ID

odoo.tools.config.parse_config(['--config=%s' % ODOO_CONF])
with odoo.api.Environment.manage():
    registry = odoo.modules.registry.RegistryManager.get(DB_NAME)
    with registry.cursor() as cr:
        ctx = odoo.api.Environment(cr, UID, {})['res.users'].context_get()
        env = odoo.api.Environment(cr, UID, ctx)
        detail_proxy = env['wsfe.request.detail']
        details_by_invoice = defaultdict(list)
        for detail in detail_proxy.search([]):
            details_by_invoice[detail.invoice_id].append(detail.id)
        with open('wsfe.pkl', 'wb') as f:
            pickle.dump(details_by_invoice, f, pickle.HIGHEST_PROTOCOL)
