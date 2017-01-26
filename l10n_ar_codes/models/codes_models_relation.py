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

from openerp import models, fields
from openerp.exceptions import Warning

class CodesModelsRelation(models.Model):
    """ 
    Intermediate table to asign models, code and apllication
    so every application that needs a specific code of a model
    doesnt have to write on the model table.
    """
    
    _name = 'codes.models.relation'

    name = fields.Char('Aplicacion', required=True)
    name_model = fields.Char('Modelo', required=True)
    id_model = fields.Integer('Id del modelo', required=True)
    code = fields.Char('Codigo / Nombre', required=True)
    
    def get_record(self):
        
        try:
            record = self.env[self.name_model].browse(self.id_model)
        except KeyError:
            raise Warning("No existe el modelo "+self.name_model)
        
        if not record:
            raise Warning("No se encontro el objeto con id: "+self.id+"para el modelo "+self.name_model)
        
        return record
    
    _sql_constraints = [
        ('Unique', 'unique(name, name_model, id_model)', "Ya existe un registro similar")
    ]
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: