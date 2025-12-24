import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

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

    team_ids = fields.One2many(
        'hr.team',
        'department_id',
        string="Teams"
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
                try:
                    department._assign_group_to_manager(manager.id)
                except (ValidationError, ValueError) as e:
                    _logger.warning(
                        "Could not assign group to manager %s for department %s: %s",
                        manager.name, department.name, str(e)
                    )

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
                        try:
                            department._remove_group_of_manager(old_manager_id)
                        except (ValidationError, ValueError) as e:
                            _logger.warning("Could not remove group from old manager: %s", str(e))
                    # Gán group mới
                    if new_manager_id:
                        try:
                            department._assign_group_to_manager(new_manager_id)
                        except (ValidationError, ValueError) as e:
                            _logger.warning("Could not assign group to new manager: %s", str(e))

        return super(HpDepartmentInherit, self).write(vals)





    def unlink(self):
        is_module_uninstall = self.env.context.get('module_uninstall', False)

        for department in self:
            if not is_module_uninstall:
                employees = self.env['hr.employee'].search([('department_id', '=', department.id)])
                if employees:
                    raise UserError(
                        _("Cannot delete department '%s' because there are still employees in this department..") % department.name
                    )

            if is_module_uninstall:
                continue 

            manager = department.manager_id
            if manager:
                try:
                    department._remove_group_of_manager(manager.id)
                except (ValidationError, ValueError):
                    pass

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
            raise ValidationError(
                _("No %(role)s group configured for department type '%(type)s' (code: %(code)s).\n\n"
                  "Please configure security groups in:\n"
                  "Configuration → Department Types → %(type)s\n\n"
                  "Add the following fields:\n"
                  "- Manager Group (XML ID)\n"
                  "- Member Group (XML ID)") % {
                    'role': role.title(),
                    'type': self.department_type_id.name,
                    'code': self.department_type_id.code,
                }
            )

        return group_xml_id
    









    def _assign_group_to_manager(self, manager_id):
        if not self.department_type_id or not self.department_type_id.exists():
            _logger.warning("Cannot assign group: department_type_id is missing or deleted for department %s", self.name)
            return

        manager = self.env['hr.employee'].sudo().browse(manager_id)
        user = manager.user_id
        if not user:
            _logger.warning("Manager %s is not associated with user. Skipping group assignment.", manager.name)
            return 
            # raise ValidationError(_("Manager is not associated with user.")) 

        try:
            group_xml_id = self._get_group_by_role(self.ROLE_MANAGER)
            if not user.has_group(group_xml_id):
                group = self.env.ref(group_xml_id, raise_if_not_found=False)
                if group:
                    user.write({'groups_id': [(4, group.id)]})
                else:
                    _logger.warning("Group XML ID %s not found in system.", group_xml_id)
        except ValidationError as e:
            # Bắt lỗi từ _get_group_by_role để không làm chết quá trình cài đặt
            _logger.warning("Skipping group assignment for dept %s: %s", self.name, str(e))








    
    def _remove_group_of_manager(self, manager_id):
        if not self.department_type_id or not self.department_type_id.exists():
            return

        manager = self.env['hr.employee'].sudo().browse(manager_id)
        count_department = self.env['hr.department'].sudo().search_count([
            ('manager_id', '=', manager_id)
        ]) 
        user = manager.user_id
        if not user or count_department > 1:
            return
        
        try:
            group_xml_id = self._get_group_by_role(self.ROLE_MANAGER)
            if user.has_group(group_xml_id):
                group = self.env.ref(group_xml_id, raise_if_not_found=False)
                if group:
                    user.write({'groups_id': [(3, group.id)]})
        except ValidationError:
            pass



            

    def _get_manager_users_by_type(self, department_type_id):
        departments = self.env['hr.department'].sudo().search([('department_type_id', '=', department_type_id)])
        employees = departments.mapped('manager_id')
        users = employees.mapped('user_id')
        return users