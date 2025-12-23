from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartnerClient(models.Model):
    _name = 'res.partner.client'
    _description = 'Partner Client'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Info Client',
        ondelete='cascade',
        required=True,
    )

    order_ids = fields.One2many(
        comodel_name='sale.order',
        inverse_name='client_id',
        string='Sale Orders',
    )

    is_sale_man_user = fields.Boolean(string="Is Sale Man", compute="_compute_is_sale_man_user", store=False)
    is_system_user = fields.Boolean(
        string="Is System User",
        compute="_compute_is_system_user",
        default=lambda self: self.env.user.has_group('base.group_system'),
    )
    sale_user_ids = fields.Many2many('res.users', compute='_compute_sale_user_ids', store=False)
    _unique_fields = ["vat", "ref", "phone"]

    @api.depends_context('uid')
    def _compute_is_sale_man_user(self):
        for client in self:
            client.is_sale_man_user = client.is_only_group_sale_salesman()


    @api.depends_context('uid')
    def _compute_is_system_user(self):
        is_system = self.env.user.has_group('base.group_system')
        for client in self:
            client.is_system_user = is_system
    
    @api.depends('branch_id')
    def _compute_sale_user_ids(self):
        sale_dept_type = self.env['department.type'].search([('code', '=', 'sale')], limit=1)
        
        current_user = self.env.user
        is_admin = current_user.has_group('base.group_system')
        # is_manager = current_user.has_group('sales_team.group_sale_manager')

        for client in self:
            if client.is_only_group_sale_salesman():
                client.sale_user_ids = current_user
                continue
            domain_emp = [('user_id', '!=', False)]
            if sale_dept_type:
                domain_emp.append(('department_id.department_type_id', '=', sale_dept_type.id))

            if client.branch_id:
                domain_emp.append(('department_id.branch_id', '=', client.branch_id.id))
            else:
                if is_admin:
                    pass 
                else:
                    client.sale_user_ids = self.env['res.users'] 
                    continue
            employees = self.env['hr.employee'].search(domain_emp)
            
            users = employees.mapped('user_id').filtered(lambda u: u.active and not u.share)

            if not is_admin:
                users = users.filtered(lambda u: not u.has_group('base.group_system'))

            client.sale_user_ids = users




    @api.onchange('user_id')
    def _onchange_user_id(self):
        if not self._origin.id:
            return
        if self.is_only_group_sale_salesman():
            self.user_id = self._origin.user_id
            raise UserError(_("Can not change saleperson"))

    @api.model_create_multi
    def create(self, vals_list):
        self._check_unique_fields(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        if any(field in vals for field in self._unique_fields):
            self._check_unique_fields([vals], is_write=True)
        return super().write(vals)

    def _check_unique_fields(self, vals_list, is_write=False):
        for vals in vals_list:
            for field in self._unique_fields:
                value = vals.get(field)
                if not value:
                    continue

                domain = [(field, "=", value)]
                if is_write:
                    domain.append(("id", "!=", self.id))

                if self.env["res.partner.client"].sudo().search_count(domain):
                    raise UserError(_("%s already exists in Client: %s") % (field.capitalize(), value))

    def is_only_group_sale_salesman(self):
        group_sale_salesman_id = self.env.ref('sales_team.group_sale_salesman').id
        group_sale_salesman_all_leads_id = self.env.ref('sales_team.group_sale_salesman_all_leads').id
        group_sale_manager_id = self.env.ref('sales_team.group_sale_manager').id
        user_group_ids = self.env.user.groups_id.ids

        return (
            group_sale_salesman_id in user_group_ids and 
            group_sale_salesman_all_leads_id not in user_group_ids and 
            group_sale_manager_id not in user_group_ids
        )

    def action_create_new_quotation(self):
        self.ensure_one()
        return {
            'name': 'New Quotation',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'context': {
                'default_client_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_pricelist_id': self.partner_id.property_product_pricelist.id,
            },
            'target': 'new',
        }
    


























    def _default_branch_id(self):
        import logging
        _logger = logging.getLogger(__name__)
        
        # Skip auto-fill for system admin
        if self.env.user.has_group('base.group_system'):
            _logger.error(f"User {self.env.user.login} is admin - skip auto-fill branch")
            return False
        
        current_user = self.env.user
        _logger.error(f"Auto-filling branch for user {current_user.login}, has employee: {bool(current_user.employee_id)}")
        
        if current_user.employee_id and current_user.employee_id.department_id:
            branch = current_user.employee_id.department_id.branch_id
            _logger.error(f"Found branch: {branch.name if branch else 'None'}")
            return branch
        
        _logger.warning(f"User {current_user.login} has no employee or department configured")
        return False




    def _default_user_id(self):
        if not self.is_only_group_sale_salesman():
            return False
        
        return self.env.user







    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        
        if not self.env.user.has_group('base.group_system'):
            if 'branch_id' in fields_list and not defaults.get('branch_id'):
                emp = self.env.user.employee_id
                if emp and emp.department_id.branch_id:
                    defaults['branch_id'] = emp.department_id.branch_id.id
        
        if self.is_only_group_sale_salesman():
            if 'user_id' in fields_list:
                defaults['user_id'] = self.env.user.id
                
        return defaults