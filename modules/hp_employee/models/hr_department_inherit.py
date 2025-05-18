from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HpDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    TYPE_SALE = 'sale'
    TYPE_PRICING = 'pricing'
    TYPE_TRUCKING = 'trucking'

    department_type = fields.Selection([
        (TYPE_SALE, 'Sale'),
        (TYPE_PRICING, 'Pricing'),
        (TYPE_TRUCKING, 'Trucking'),
    ], string='Department Type', required=True)

    @api.model_create_multi
    def create(self, vals_list):
        departments = super().create(vals_list)
        for department in departments:
            manager = department.manager_id
            if manager:
                department._assign_group_to_manager(manager.id, department.department_type, 'manager')
                
        return departments

    def write(self, vals):
        for department in self:
            if 'department_type' in vals:
                if department.department_type:
                    raise UserError(_("You cannot modify the Department Type once it's set."))
            
            if 'manager_id' in vals:
                old_manager_id = department.manager_id.id if department.manager_id else False
                new_manager_id = vals.get('manager_id')
                if new_manager_id != old_manager_id:
                    department.department_type = department.department_type if department.department_type else vals.get('department_type')
                    department._remove_group_of_manage(old_manager_id, department.department_type, 'manager')
                    department._assign_group_to_manager(new_manager_id, department.department_type, 'manager')

        return super(HpDepartmentInherit, self).write(vals)

    def unlink(self):
        for department in self:
            employees = self.env['hr.employee'].search([('department_id', '=', department.id)])
            if employees:
                raise UserError(
                    _("Cannot delete department '%s' because there are still employees in this department..") % department.name
                )

            manager = department.manager_id
            if manager:
                department._remove_group_of_manage(manager.id, department.department_type, 'manager')
            
        return super().unlink()
    
    def _get_group_by_type(self, department_type, role='member'):
        group_map = {
            'manager': {
                self.TYPE_SALE: 'sales_team.group_sale_salesman_all_leads',
                self.TYPE_PRICING: 'hp_pricing.group_hp_pricing_lead',
            },
            'member': {
                self.TYPE_SALE: 'sales_team.group_sale_salesman',
                self.TYPE_PRICING: 'hp_pricing.group_hp_pricing_member',
            }
        }

        group_dict = group_map.get(role)
        if not group_dict:
            raise ValidationError(_(f"Unknown group role: {role}"))

        group_xml_id = group_dict.get(department_type)
        if not group_xml_id:
            raise ValidationError(_(f"Unknown group {role} for department type: {department_type}"))

        return group_xml_id
    
    def _assign_group_to_manager(self, manager_id, department_type, role):
        manager = self.env['hr.employee'].sudo().browse(manager_id)
        user = manager.user_id
        if not user:
            raise ValidationError(_("Manager is not associated with user."))

        group_xml_id = self._get_group_by_type(department_type, role)
        if not user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(4, group.id)]})
    
    def _remove_group_of_manage(self, manager_id, department_type, role):
        manager = self.env['hr.employee'].sudo().browse(manager_id)
        user = manager.user_id
        if not user:
            return
        
        group_xml_id = self._get_group_by_type(department_type, role)
        if user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(3, group.id)]})
            
    def _get_manage_user_by_type(self, department_type):
        departments = self.env['hp.department'].sudo().search([('department_type', '=', department_type)])
        employees = departments.mapped('manager_id')
        users = employees.mapped('user_id')
        return users