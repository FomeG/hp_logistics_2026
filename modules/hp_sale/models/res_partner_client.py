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
    sale_user_ids = fields.Many2many('res.users', compute='_compute_sale_user_ids', store=False)

    _unique_fields = ["vat", "ref", "phone"]

    @api.depends()
    def _compute_is_sale_man_user(self):
        for client in self:
            client.is_sale_man_user = client.is_only_group_sale_salesman()
    
    @api.depends()
    def _compute_sale_user_ids(self):
        group = self.env.ref('sales_team.group_sale_salesman')
        users = self.env['res.users'].search([
            ('groups_id', 'in', [group.id]),
            ('share', '=', False),
            ('id', '!=', self.env.ref('base.user_admin').id)
        ])
        for client in self:
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
    