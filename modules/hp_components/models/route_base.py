from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RouteBase(models.Model):
    _name = "route.base"
    _inherit = ['unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Route Base"

    name = fields.Char(
        compute='_compute_name',
        store=True,
        string="Name",
        tracking=True,
    )

    from_location_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        string='From Location',
        tracking=True,
        domain=[('type', '=', 'route_point')],
    )

    from_state_id = fields.Many2one(
        related='from_location_id.state_id',
        readonly=True,
        string='From Province',
    )

    to_location_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        string='To Location',
        tracking=True,
        domain=[('type', '=', 'route_point')],
    )

    to_state_id = fields.Many2one(
        related='to_location_id.state_id',
        readonly=True,
        string='To Province',
    )

    direction = fields.Selection([
        ('export', 'Export'),
        ('import', 'Import'),
    ], default='export', string='Direction', tracking=True)

    distance_km = fields.Float(
        required=True,
        string='Distance KM',
        tracking=True,
    )

    @api.depends('from_location_id', 'to_location_id')
    def _compute_name(self):
        for route in self:
            if route.from_location_id and route.to_location_id:
                route.name = f"{route.from_location_id.name} - {route.to_location_id.name}"
            else:
                route.name = "New Route"

    @api.constrains('from_location_id', 'to_location_id')
    def _check_unique_route_pair(self):
        for route in self:
            if route.from_location_id == route.to_location_id:
                raise ValidationError("Origin and destination must be different.")
            existing_route = self.search([
                ('id', '!=', route.id),
                '|',
                '&', ('from_location_id', '=', route.from_location_id.id),
                ('to_location_id', '=', route.to_location_id.id),
                '&', ('from_location_id', '=', route.to_location_id.id),
                ('to_location_id', '=', route.from_location_id.id),
            ])
            if existing_route:
                raise ValidationError(
                    f"A route between {route.from_location_id.name} and "
                    f"{route.to_location_id.name} already exists."
                )

    _sql_constraints = [
        ('from_different_to',
         "CHECK (from_location_id != to_location_id)",
         "Origin and destination must be different"),
    ]