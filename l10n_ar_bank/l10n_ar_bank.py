# -*- coding: utf-8 -*-
from openerp.osv import fields,osv
from openerp.tools.translate import _
import time

class Bank(osv.osv):
    
    _inherit = 'res.bank'
    _columns = {
        'vat': fields.char(_('VAT'),size=32 ,help="Value Added Tax number."),
    }

    def name_search(self, cr, uid, name, args, domain=None, operator='ilike',context=None, limit=80):

        ids = []

        if name:

            ids =  self.search(cr, uid, [('bic', operator , name)] + args, limit=limit, context=context)

        if not ids:

            ids =  self.search(cr, uid, [('name', operator , name)] + args, limit=limit, context=context)

        return self.name_get(cr,uid,ids)
    
Bank()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
