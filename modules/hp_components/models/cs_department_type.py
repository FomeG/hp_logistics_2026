from odoo import models, fields, api
class CSDepartmentType(models.Model):
    _name = "cs.department.type"
    _description = "Department Type"
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']
    name = fields.Char(string="Name", required=True)