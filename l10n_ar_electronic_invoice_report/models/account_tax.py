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

from openerp import models, _


class AccountTax(models.Model):

    _inherit = 'account.tax'

    def get_tax_description(self):

        group_vat = self.env.ref('l10n_ar.tax_group_vat')
        # EJ: IVA 21%
        res = _('VAT ') + str(self.amount) + '%:' if self.tax_group_id == group_vat else self.description

        return res
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: