from odoo import models, fields

class HpDepartment(models.Model):
    _name = 'hp.department'
    _description = 'Phòng ban'

    name = fields.Char(string='Name of Department',required=True)
