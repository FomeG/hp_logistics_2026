from odoo import models, fields, api


class FreightPurchaseRoute(models.Model):
    _name = 'freight.purchase.route'
    _description = 'Route'

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Route Name',compute='_compute_route_name',store=True,index=True,tracking=True)
    pol_id = fields.Many2one('freight.purchase.port', domain="[('is_pod', '=', False)]", required=True,tracking=True)
    pod_id = fields.Many2one('freight.purchase.port', domain="[('is_pod', '=', True)]", required=True,tracking=True)
    region_id = fields.Many2one(related='pod_id.region_id', store=True,tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True,tracking=True)

    @api.depends('pol_id', 'pod_id')
    def _compute_route_name(self):
        for route in self:
            if route.pod_id and route.pol_id:
                route.name = f"{route.pol_id.name} → {route.pod_id.name}"
            else:
                route.name = False
            

    # Constraints
    @api.constrains('pol_id', 'pod_id')
    def _check_ports(self):
        for route in self:
            if route.pol_id == route.pod_id:
                raise models.ValidationError("POL and POD cannot be the same!")
