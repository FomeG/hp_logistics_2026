from odoo.addons.hp_employee.models.hr_department_inherit import HpDepartmentInherit

class DepartmentService:
    _name = 'custom_component.department.service'

    DEPARTMENT_TYPE_SALE = 'sale'
    DEPARTMENT_TYPE_PRICING = 'pricing'

    def __init__(self, env):
        self.env = env

    def _get_department_leader_by_type(self, department_type):
        department = self.env['hr.department'].search([('department_type', '=', department_type)], limit=1)
        if department and department.manager_id and department.manager_id.user_id:
            return department.manager_id.user_id  # returns res.users record
        return False  # or raise an error if required

    def get_pricing_department_leader(self):
        return self._get_department_leader_by_type(HpDepartmentInherit.TYPE_PRICING)
    
    def get_sale_department_leader(self):
        return self._get_department_leader_by_type(HpDepartmentInherit.TYPE_SALE)