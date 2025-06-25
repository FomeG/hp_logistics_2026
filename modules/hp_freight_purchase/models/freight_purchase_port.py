from pkg_resources import require

from odoo import models, fields,api

from odoo.exceptions import ValidationError

class FreightPurchasePort(models.Model):
    _name = 'freight.purchase.port'
    _description = 'Port'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    is_local = fields.Boolean(
        string='Is Local Port',
        required=False,
        default=False,
        tracking=True
    )
    region_id = fields.Many2one(
        'freight.purchase.region',
        string='Region',
        required=True,
        tracking=True
    )
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    employees = fields.Char(
        string="Employees in Region",
        compute='_compute_region_employees',
        store=False
    )

    @api.constrains('region_id')
    def _check_region_required(self):
        for record in self:
            if not record.region_id:
                raise ValidationError("Region is required for the port.")

    @api.depends('region_id.employee_ids')
    def _compute_region_employees(self):
        for port in self:
            if port.region_id and port.region_id.employee_ids:
                port.employees = ", ".join(port.region_id.employee_ids.mapped('name'))
            else:
                port.employees = ""