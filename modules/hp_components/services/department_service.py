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
    
    def buil_name_trucking_plan(self, plan_name):
        current_user = self.env.user
        employee = self.env['hr.employee'].sudo().search([('user_id', '=', current_user.id)], limit=1)
        if not employee or not employee.department_id or employee.department_id.department_type != self.DEPARTMENT_TYPE_TRUCKING:
            return plan_name
        
        department_area = employee.department_id.department_area
        if not department_area:
            return plan_name

        area_upper = department_area.upper()
        new_name = plan_name.replace('PLAN', area_upper)

        return new_name
        
