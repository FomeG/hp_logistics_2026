from odoo import models, fields, api


class FreightPurchaseRoute(models.Model):
    _name = 'freight.purchase.route'
    _description = 'Route'

    name = fields.Char(string='Route Name',compute='_compute_route_name',store=True,index=True)
    pol_id = fields.Many2one('freight.purchase.port', domain="[('is_pod', '=', False)]", required=True)
    pod_id = fields.Many2one('freight.purchase.port', domain="[('is_pod', '=', True)]", required=True)
    region_id = fields.Many2one(related='pod_id.region_id', store=True)
    is_active = fields.Boolean(string='Is Active', default=True)

    @api.depends('pol_id', 'pod_id')
    def _compute_route_name(self):
        for route in self:
            route.name = f"{route.pol_id.code} → {route.pod_id.code}"

    # Constraints
    @api.constrains('pol_id', 'pod_id')
    def _check_ports(self):
        for route in self:
            if route.pol_id == route.pod_id:
                raise models.ValidationError("POL and POD cannot be the same!")
