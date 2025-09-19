from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HpDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    TYPE_SALE = 'SALE'
    TYPE_PRICING = 'PRICING'
    TYPE_TRUCKING = 'TRUCKING'

    ROLE_MANAGER = 'manager'
    ROLE_MEMBER = 'member'

    ARRAY_TYPE = [TYPE_SALE, TYPE_PRICING, TYPE_TRUCKING]

    # department_type = fields.Selection([
    #     (TYPE_SALE, 'Sale'),
    #     (TYPE_PRICING, 'Pricing'),
    #     (TYPE_TRUCKING, 'Trucking'),
    # ], string='Department Type', required=True)

    @api.model
    def can_create_department(self):
        count = self.sudo().search_count([('department_type_id', 'in', self.ARRAY_TYPE)])
        return count < len(self.ARRAY_TYPE)
    department_type_id = fields.Many2one(
        'department.type', string='Department Type', required=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            dept_type = vals.get('department_type_id')
            if dept_type:
                existing = self.sudo().search([('department_type_id', '=', dept_type)], limit=1)
                if existing:
                    raise ValidationError(f"Department with type '{dept_type}' already exists.")

        departments = super().create(vals_list)
        for department in departments:
            manager = department.manager_id
            if manager:
                department._assign_group_to_manager(manager.id)
                
        return departments

    def write(self, vals):
        for department in self:
            if 'department_type_id' in vals:
                if department.department_type_id and department.department_type_id.id != vals.get('department_type_id'):
                    raise UserError(_("You cannot modify the Department Type once it's set."))

            if 'manager_id' in vals:
                old_manager_id = department.manager_id.id if department.manager_id else False
                new_manager_id = vals.get('manager_id')
                if new_manager_id != old_manager_id:
                    # Xoá group cũ
                    if old_manager_id:
                        department._remove_group_of_manage(old_manager_id)
                    # Gán group mới
                    if new_manager_id:
                        department._assign_group_to_manager(new_manager_id)

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
                department._remove_group_of_manage(manager.id)
            
        return super().unlink()
    
    def _get_group_by_role(self, role):
        group_map = {
            self.ROLE_MANAGER: {
                self.TYPE_SALE: 'sales_team.group_sale_salesman_all_leads',
                self.TYPE_PRICING: 'hp_freight_purchase.group_hp_freight_purchase_lead',
                self.TYPE_TRUCKING: 'hp_trucking_planning.group_hp_trucking_planning_lead',
            },
            self.ROLE_MEMBER: {
                self.TYPE_SALE: 'sales_team.group_sale_salesman',
                self.TYPE_PRICING: 'hp_freight_purchase.group_hp_freight_purchase_member',
                self.TYPE_TRUCKING: 'hp_trucking_planning.group_hp_trucking_planning_member',
            }
        }

        group_dict = group_map.get(role)
        if not group_dict:
            raise ValidationError(_(f"Unknown group role: {role}"))

        group_xml_id = group_dict.get(self.department_type_id.code)
        if not group_xml_id:
            raise ValidationError(_(f"Unknown group {role} for department type: {self.department_type_id}"))

        return group_xml_id
    
    def _assign_group_to_manager(self, manager_id):
        manager = self.env['hr.employee'].sudo().browse(manager_id)
        user = manager.user_id
        if not user:
            raise ValidationError(_("Manager is not associated with user."))

        group_xml_id = self._get_group_by_role(self.ROLE_MANAGER)
        if not user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(4, group.id)]})
    
    def _remove_group_of_manage(self, manager_id):
        manager = self.env['hr.employee'].sudo().browse(manager_id)
        count_department = self.env['hr.department'].sudo().search_count([
            ('manager_id', '=', manager_id)
        ]) 
        user = manager.user_id
        if not user or count_department > 1:
            return
        
        group_xml_id = self._get_group_by_role(self.ROLE_MANAGER)
        if user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(3, group.id)]})

    def _get_manager_users_by_type(self, department_type_id):
        departments = self.env['hr.department'].sudo().search([('department_type_id', '=', department_type_id)])
        employees = departments.mapped('manager_id')
        users = employees.mapped('user_id')
        return users