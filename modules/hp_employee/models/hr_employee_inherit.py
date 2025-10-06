from odoo import models, api, fields, _
from ...hp_components.models import constants
from odoo.exceptions import ValidationError, UserError

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    dept_manager_id = fields.Many2one('hr.employee', compute='_compute_manager_id', store=False)

    work_shift_id = fields.Many2one(
        comodel_name="hr.work.shift",
        string="Work Shift",
        default=lambda self: self.env['hr.work.shift'].search([('shift_type', '=', constants.WorkShiftType.FIXED)], limit=1)
    )

    @api.depends('department_id')
    def _compute_manager_id(self):
        for employee in self:
            employee.dept_manager_id = employee.department_id.manager_id if employee.department_id else False
                

    @api.model_create_multi
    def create(self, vals_list):
        emails = {vals.get('work_email') for vals in vals_list if vals.get('work_email')}
        phones = {vals.get('work_phone') for vals in vals_list if vals.get('work_phone')}

        existing_emails = self.env['hr.employee'].sudo().search([('work_email', 'in', list(emails))]).mapped('work_email')
        existing_phones = self.env['hr.employee'].sudo().search([('work_phone', 'in', list(phones))]).mapped('work_phone')

        duplicate_emails = list(set(existing_emails) & emails)
        duplicate_phones = list(set(existing_phones) & phones)

        valid_vals = [
            vals for vals in vals_list
            if vals.get('work_email') not in duplicate_emails and vals.get('work_phone') not in duplicate_phones
        ]

        created_records = self.env['res.partner'].browse()
        if valid_vals:
            created_records = super().create(valid_vals)
            self.env.cr.commit()

            for employee in created_records:
                department = employee.department_id
                if department:
                    employee._assign_group_to_member(department)

        if duplicate_emails or duplicate_phones:
            message_parts = []
            if duplicate_emails:
                message_parts.append(_("Email is exist: %s") % ", ".join(duplicate_emails))
            if duplicate_phones:
                message_parts.append(_("Phone is exist: %s") % ", ".join(duplicate_phones))
            raise UserError("\n".join(message_parts))

        return created_records
    
    def write(self, vals):
        # Check for duplicate emails and phones
        for field in ['work_email', 'work_phone']:
            value = vals.get(field)
            if value:
                conflict = self.search([
                    ('id', 'not in', self.ids),
                    (field, '=', value)
                ], limit=1)
                if conflict:
                    raise UserError(_("%s '%s' is already used by another employee.") % (field.replace('_', ' ').title(), value))
        
        # Handle department changes
        if 'department_id' in vals:
            for employee in self:
                old_department = employee.department_id
                new_department_id = vals.get('department_id')
                if old_department.id != new_department_id:
                    employee._remove_group_of_member(old_department)
                    new_department = self.env['hr.department'].sudo().browse(new_department_id)
                    employee._assign_group_to_member(new_department)

        # Sync employee changes to user (if user exists and values are different)
        sync_fields = {}
        for employee in self:
            if employee.user_id:
                if 'name' in vals and vals['name'] and vals['name'] != employee.user_id.name:
                    sync_fields['name'] = vals['name']
                if 'work_email' in vals and vals['work_email'] and vals['work_email'] != employee.user_id.email:
                    sync_fields['email'] = vals['work_email']
                if 'mobile_phone' in vals and vals['mobile_phone'] and vals['mobile_phone'] != employee.user_id.phone:
                    sync_fields['phone'] = vals['mobile_phone']
        
        # Perform the employee update first
        result = super().write(vals)
        
        # Then sync to user if needed
        if sync_fields:
            for employee in self:
                if employee.user_id:
                    employee.user_id.write(sync_fields)
        
        return result

    @api.depends('address_id')
    def _compute_phones(self):
        for employee in self:
            employee.work_phone = False

    def action_create_user_full(self):
        self.ensure_one()
        if self.user_id:
            raise ValidationError(_("This employee already has an user."))
        
        return {
                'name': _('Create User'),
                'type': 'ir.actions.act_window',
                'res_model': 'res.users',
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_users_form').id,
                'target': 'new',
                'context': dict(self._context, **{
                    'default_create_employee_id': self.id,
                    'default_name': self.name,
                    'default_phone': self.work_phone,
                    'default_mobile': self.mobile_phone,
                    'default_login': self.work_email,
                    'default_partner_id': self.work_contact_id.id,
                    # Use a custom context to override default groups behavior
                    'employee_user_creation': True,
            })
        }

    def _assign_group_to_member(self, department):
        user = self.user_id
        if not user or not department:
            return

        group_xml_id = department._get_group_by_role(department.ROLE_MEMBER)
        if not user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(4, group.id)]})
    
    def _remove_group_of_member(self, department):
        user = self.user_id
        if not user or not department:
            return

        group_xml_id = department._get_group_by_role(department.ROLE_MEMBER)
        if user.has_group(group_xml_id):
            group = self.env.ref(group_xml_id)
            user.write({'groups_id': [(3, group.id)]})
