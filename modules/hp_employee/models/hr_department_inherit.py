from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class HpDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    # TYPE_SALE = 'sale'
    # TYPE_PRICING = 'pricing'
    # TYPE_TRUCKING = 'trucking'
    # TYPE_CS = 'cs'

    ROLE_MANAGER = 'manager'
    ROLE_MEMBER = 'member'

    # ARRAY_TYPE = [TYPE_SALE, TYPE_PRICING, TYPE_TRUCKING, TYPE_CS]

    name = fields.Char(
        string='Department Name',
        compute='_compute_department_name',
        required=False,
        store=True,
    )

    branch_id = fields.Many2one(
        comodel_name='hr.branch',
        index=True,
    )

    department_type_id = fields.Many2one(
        comodel_name='department.type',
        string='Department Type',
        ondelete='cascade',
    )

    _sql_constraints = [
        (
            'uniq_department_branch_type',
            'unique(department_type_id, branch_id)',
            'Each branch can only have one department of the same type.'
        )
    ]

    @api.model
    def can_create_department(self, branch_id=None):
        # count = self.sudo().search_count([('department_type_id', 'in', self.ARRAY_TYPE)])
        # return count < len(self.ARRAY_TYPE)
        all_types = self.env['department.type'].search([])

        if not branch_id:
            return len(all_types) > 0

        used_types = self.sudo().search([
            ('branch_id', '=', branch_id)
        ]).mapped('department_type_id')

        return len(used_types) < len(all_types)

    @api.depends('department_type_id', 'branch_id')
    def _compute_department_name(self):
        for record in self:
            if record.department_type_id and record.branch_id:
                record.name = record.department_type_id.name + ' ' + record.branch_id.name
            else:
                record.name = ''

    @api.model_create_multi
    def create(self, vals_list):
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

    def copy(self, default=None):
        default = dict(default or {})
        default.update({
            'name': "New Department",
            'branch_id': False,
        })
        return super().copy(default)
    
    def _get_group_by_role(self, role):
        if role == self.ROLE_MANAGER:
            group_xml_id = self.department_type_id.manager_group_xml_id
        elif role == self.ROLE_MEMBER:
            group_xml_id = self.department_type_id.member_group_xml_id
        else:
            raise ValidationError(_(f"Unknown group role: {role}"))

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