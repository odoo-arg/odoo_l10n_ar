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
    Intermediate table to assign models, code and application
    so every application that needs a specific code of a model
    doesn't have to write on the model table.
    """
    
    _name = 'codes.models.relation'

    name = fields.Char('Aplicacion', required=True)
    name_model = fields.Char('Modelo', required=True)
    id_model = fields.Integer('Id del modelo', required=True)
    code = fields.Char('Codigo / Nombre', required=True)

    company_id = fields.Many2one(
        'res.company',
        'Compania',
        required=True,
        default=lambda self: self.env.user.company_id
    )

    def get_record_from_code(self, name_model, code, name='Afip'):
        """
        Busca el objeto segun el codigo de la aplicacion
        :param name: Aplicacion (ej: Afip)
        :param name_model: Nombre del modelo (ej: account.invoice)
        :param code: Codigo de la aplicacion
        :return: record del objeto del name_model
        """
        record = self.search([
            ('name', '=', name),
            ('name_model', '=', name_model),
            ('code', '=', code)
        ], limit=1)

        if not record:
            raise Warning('No se encontro instancia para: \n Aplicacion {0}:'
                          '\nModelo: {1}\nCodigo: {2}'.format(name, name_model, code))

        return record.get_record()

    def get_code(self, name_model, id_model, name='Afip'):
        """
        Busca el codigo de la aplicacion para los parametros definidos
        :param name: Aplicacion (ej: Afip)
        :param name_model: Nombre del modelo (ej: account.invoice)
        :param id_model: Id a buscar
        :return: Codigo de la aplicacion
        """
        record = self.search([
            ('name', '=', name),
            ('name_model', '=', name_model),
            ('id_model', '=', id_model)
        ], limit=1)

        if not record:
            raise Warning('No se encontro codigo para: \n Aplicacion {0}:'
                          '\nModelo: {1}\nId: {2}'.format(name, name_model, id_model))

        return record.code

    def get_record(self):
        ''' 
        :return record: Objeto del modelo "name_model" con id "id_model"
        '''
        
        try:
            record = self.env[self.name_model].browse(self.id_model)
        except KeyError:
            raise Warning("No existe el modelo {}".format(self.name_model))
        
        if not record:
            raise Warning("No se encontro el objeto con id: {} para el modelo {}".format(self.id_model, self.name_model))
        
        return record
    
    _sql_constraints = [
        ('Unique', 'unique(name, name_model, id_model)', "Ya existe un registro similar")
    ]
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: