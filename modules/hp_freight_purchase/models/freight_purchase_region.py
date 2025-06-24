from odoo import models, fields, api

class FreightPurchaseRegion(models.Model):
    _name = 'freight.purchase.region'
    _description = 'Region'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)
    ports = fields.One2many('freight.purchase.port','region_id',string='Ports', tracking=True)
    employee_ids = fields.Many2many('hr.employee', string='Pricing Members', tracking=True)

    employee_string = fields.Char(string="Employees in Region", compute='_compute_employee_string', store=False)
    port_string = fields.Char(string="Ports in Region", compute='_compute_port_string', store=False)

    @api.depends('employee_ids')
    def _compute_employee_string(self):
        for region in self:
            if region.employee_ids:
                region.employee_string = ", ".join(region.employee_ids.mapped('name'))
            else:
                region.employee_string = ""

    @api.depends('ports')
    def _compute_port_string(self):
        for region in self:
            if region.ports:
                region.port_string = ", ".join(region.ports.mapped('name'))
            else:
                region.port_string = ""