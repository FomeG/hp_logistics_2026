from odoo import models, api


class UserServiceInherit(models.AbstractModel):
    _name = 'hp_employee.user.service'
    _inherit = 'hp_components.user.service'
    _description = 'User Service Inherit'

    @api.model
    def get_user_teams(self, user=None):
        user = user or self.env.user
        return self.env['hr.team'].search([
            ('user_ids', 'in', user.id)
        ])

    @api.model
    def inject_user_teams_domain(self, domain=None, user=None):
        domain = list(domain or [])
        teams = self.get_user_teams(user)
        if not teams:
            if super().is_admin_user(user):
                return domain
        domain.append(('team_id', 'in', teams.ids))
        return domain


    @api.model
    def is_hr_director(self, user=None):
        """Check if user is HR Director"""
        return self._check_user_has_group('hp_employee.group_hr_director', user.id if user else None)

    @api.model
    def is_hr_team_manager(self, user=None):
        """Check if user is HR Team Manager"""
        return self._check_user_has_group('hp_employee.group_hr_lead', user.id if user else None)

    @api.model
    def is_hr_user(self, user=None):
        """Check if user is HR User (member)"""
        return self._check_user_has_group('hp_employee.group_hr_user', user.id if user else None)

    @api.model
    def is_hr_role(self, user=None):
        """Check if user has any HR role"""
        return self.is_hr_director(user) or self.is_hr_team_manager(user) or self.is_hr_user(user)


    @api.model
    def can_see_employee(self, employee, user=None):
        """
        Check if user can see employee
        All users can read all employees
        """
        return True

    @api.model
    def can_edit_employee(self, employee, user=None):
        """
        Check if user can edit employee
        - Admin: can edit all
        - HR Director: can edit all in their branch (except other directors)
        - HR Team Manager: can edit all in their branch (except directors and other managers)
        - HR User: can edit only non-HR staff in their branch
        - Non-HR users: cannot edit anyone
        """
        user = user or self.env.user

        # Admin can edit all
        if self.is_admin_user(user.id):
            return True

        # Non-HR users cannot edit anyone
        if not self.is_hr_role(user):
            return False

        # Must have employee record with department
        if not user.employee_id or not user.employee_id.department_id:
            return False

        # Must be same branch
        user_branch = user.employee_id.department_id.branch_id
        employee_branch = employee.department_id.branch_id
        if not user_branch or not employee_branch or user_branch.id != employee_branch.id:
            return False

        # Check hierarchy based on user's HR role
        target_user = employee.user_id
        if not target_user:
            # No user linked, can edit
            return True

        # HR User (member) - can edit other HR members, but not Team Managers or Directors
        if self.is_hr_user(user) and not self.is_hr_team_manager(user):
            # Cannot edit Team Manager
            if target_user.has_group('hp_employee.group_hr_lead'):
                return False
            # Cannot edit Director
            if target_user.has_group('hp_employee.group_hr_director'):
                return False
            # Can edit other HR members and non-HR staff
            return True

        # HR Team Manager cannot edit Directors or other Managers
        if self.is_hr_team_manager(user) and not self.is_hr_director(user):
            # Cannot edit Director
            if target_user.has_group('hp_employee.group_hr_director'):
                return False
            # Cannot edit other Team Managers
            if target_user.has_group('hp_employee.group_hr_lead'):
                return False
            return True

        # HR Director cannot edit other Directors
        if self.is_hr_director(user):
            if target_user.has_group('hp_employee.group_hr_director'):
                return False
            return True

        return True

    @api.model
    def can_create_employee(self, user=None):
        """
        Check if user can create employee
        - Admin: can create
        - HR Director/Team Manager/User: can create
        - Others: cannot create
        """
        user = user or self.env.user

        # Admin can create
        if self.is_admin_user(user.id):
            return True

        # HR users can create
        return self.is_hr_role(user)

    @api.model
    def can_delete_employee(self, employee, user=None):
        """
        Check if user can delete employee
        - Admin: can delete all
        - HR Director/Team Manager: can delete employees in their branch
        - HR User: cannot delete
        - Others: cannot delete
        """
        user = user or self.env.user

        # Admin can delete all
        if self.is_admin_user(user.id):
            return True

        # HR User (member) cannot delete
        if self.is_hr_user(user) and not self.is_hr_team_manager(user):
            return False

        # HR Director/Team Manager can delete employees in their branch
        if not user.employee_id or not user.employee_id.department_id:
            return False

        user_branch = user.employee_id.department_id.branch_id
        employee_branch = employee.department_id.branch_id

        return user_branch and employee_branch and user_branch.id == employee_branch.id

