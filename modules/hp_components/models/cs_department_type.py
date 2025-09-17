from odoo import models, fields, api
class CSDepartmentType(models.Model):
    _name = "cs.department.type"
    _description = "Department Type"

    name = fields.Char(string="Name", required=True)
    code = fields.Char(string="Code", required=True)
