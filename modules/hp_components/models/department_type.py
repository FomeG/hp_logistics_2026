from odoo import models, fields, api
class DepartmentType(models.Model):
    _name = "department.type"
    _description = "Department Type"
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin']

    name = fields.Char(string="Name", required=True)

    manager_group_xml_id = fields.Char(
        string="Manager Group (XML ID)",
        help="Security group XML ID for department managers (e.g., 'hp_customer_service.group_hp_customer_service_leader')",
    )

    member_group_xml_id = fields.Char(
        string="Member Group (XML ID)",
        help="Security group XML ID for department members (e.g., 'hp_customer_service.group_hp_customer_service_member')",
    )