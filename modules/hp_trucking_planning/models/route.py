from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Route(models.Model):
    _name = "trucking_planning.route"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Route"

    name = fields.Char(
        compute='_compute_name',
        store=True,
        string="Name",
        tracking=True,
    )
    from_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        required=True,
        string='From Location',
        tracking=True,
        domain=[('type', '=', 'route_point')],
    )
    from_state_id = fields.Many2one(
        related='from_location_id.state_id',
        readonly=True,
    )
    to_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        required=True,
        string='To Location',
        domain=[('type', '=', 'route_point')],
    )
    to_state_id = fields.Many2one(
        related='to_location_id.state_id',
        readonly=True,
    )
    extra_fuel = fields.Boolean(
        compute='_compute_extra_fuel',
    )

    road_fee = fields.Float(
        required=True,
        string='Road Fee',
        tracking=True,
    )
    trip_salary = fields.Float(
        required=True,
        string='Trip Salary',
        tracking=True,
    )
    total_cost = fields.Float(
        compute='_compute_total_cost',
        readonly=True,
        string='Total Cost',
        tracking=True,
    )
    ticket_fee = fields.Float(
        required=True,
        string='Ticket Fee',
        tracking=True,
    )
    distance_km = fields.Float(
        required=True,
        string='Distance KM',
        tracking=True,
    )
    direction = fields.Selection([
        ('export','Export'),
        ('import','Import'),
    ],default='export',)

    @api.depends('road_fee','trip_salary')
    def _compute_total_cost(self):
        for route in self:
            route.total_cost = route.road_fee + route.trip_salary

    @api.depends('from_location_id.state_id', 'to_location_id.state_id')
    def _compute_extra_fuel(self):
        for route in self:
            route.extra_fuel = route.from_location_id.extra_fuel == True or route.to_location_id.extra_fuel == True

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
        # Prevent from and to being the same
        ('from_different_to',
         "CHECK (from_location_id != to_location_id)",
         "Origin and destination must be different"),
    ]