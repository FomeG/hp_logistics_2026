from odoo.addons.component.core import Component
from odoo import tools

class HrEmployeeListener(Component):
    _name = "hr.employee.listener"
    _description = "Hr Employee listener"
    _inherit = 'base.event.listener'
    _apply_on = ['hr.employee']

    def on_record_create(self, record, fields=None):
        department = record.department_id
        if not department or not department.department_type_id:
            return
        
        department_type = department.department_type_id
        is_manager = self.env['hr.department'].search_count([
            ('manager_id', '=', record.id),
            ('department_type_id.code', '=', department_type.code),
        ]) > 0

        group_xml_id = department_type.member_group_xml_id
        if is_manager:
            group_xml_id = department_type.manager_group_xml_id

        default_password = tools.config.get('default_user_password', 'hp@2025')
        user_vals = {
            'name': record.name,
            'login': record.work_email or record.name.replace(" ", "").lower(),
            'email': record.work_email,
            'employee_id': record.id,
            'password': default_password,
        }
        user = self.env['res.users'].create(user_vals)
        if group_xml_id:
            group = self.env.ref(group_xml_id)
            if group:
                user.write({'groups_id': [(6, 0, [group.id])]})

        record.update({
            'user_id': user.id,
        })

        return user