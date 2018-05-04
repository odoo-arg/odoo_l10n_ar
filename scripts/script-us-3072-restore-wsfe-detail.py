import pickle

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
        invoice_proxy = env['account.invoice']
        with open('wsfe.pkl', 'rb') as f:
            dict = pickle.load(f)
        for inv_id, det_ids in dict.iteritems():
            invoice_proxy.browse(inv_id).write({
                'wsfe_request_detail_ids': [(6, 0, det_ids)]
            })
