from odoo.addons.hp_employee.models.hr_department_inherit import HpDepartmentInherit

class DepartmentService:
    _name = 'custom_component.department.service'

    DEPARTMENT_TYPE_SALE = 'sale'
    DEPARTMENT_TYPE_PRICING = 'pricing'
    DEPARTMENT_TYPE_TRUCKING = 'trucking'

    TRUCKING_AREA_HN = 'hn'
    TRUCKING_AREA_HP = 'hp'
    TRUCKING_AREA_SG = 'sg'

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

    def get_user_by_department_type(self, department_type, branch_id=False):
        domain = [
            ('department_id.department_type_id.code', '=', department_type),
            ('user_id', '!=', False),
        ]

        if branch_id:
            domain.append(('department_id.branch_id', '=', branch_id))

        return self.env['hr.employee'].sudo().search(domain).mapped('user_id')
    
    def get_department_leader_by_employee(self, employee):
        if not employee.department_id:
            return False
        
        department = employee.department_id
        return department.manager_id.user_id if department.manager_id else False