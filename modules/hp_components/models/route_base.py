from odoo import models, fields, api, _
from odoo.api import onchange, ValuesType, Self
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

class RouteBase(models.Model):
    _name = "route.base"
    _inherit = ['unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Route For Truck Freight"

    name = fields.Char(
        compute='_compute_name',
        store=True,
        string="Name",
        tracking=True,
    )
    route_level = fields.Selection(
        constants.RouteLevel.SELECT_OPTIONS,
        default=constants.RouteLevel.INTERNATIONAL,
        tracking=True,
        required=True,
        compute='_compute_route_level',
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        string='From Location',
        tracking=True,
        index=True,
        ondelete='cascade'
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
        index=True,
        ondelete='cascade'
    )

    to_state_id = fields.Many2one(
        related='to_location_id.state_id',
        readonly=True,
        string='To Province',
    )

    direction = fields.Selection([
        ('export', 'Export'),
        ('import', 'Import'),
        ('other', 'Other'),
    ], default='export',
        string='Direction',
        tracking=True,
        compute='_compute_direction',
    )

    distance_km = fields.Float(
        required=False,
        string='Distance KM',
        tracking=True,
    )
    extra_fuel = fields.Boolean(
        compute='_compute_extra_fuel',
    )
    road_fee = fields.Float(
        required=False,
        string='Road Fee',
        tracking=True,
    )
    trip_salary = fields.Float(
        required=False,
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
        required=False,
        string='Ticket Fee',
        tracking=True,
    )

    region_id = fields.Many2one(
        comodel_name='region',
        compute='_compute_region_id',
        readonly=True,
        store=True,
        index=True,
    )
    parent_id = fields.Many2one(
        comodel_name='route.base',
        string='Parent Route',
        ondelete='set null',
    )
    children_ids = fields.One2many(
        comodel_name='route.base',
        inverse_name='parent_id',
        string='Child Routes',
    )

    @api.depends('from_location_id', 'to_location_id')
    def _compute_name(self):

        for route in self:
            if route.from_location_id and route.to_location_id:
                route.name = f"{route.from_location_id.name} -> {route.to_location_id.name}"
            else:
                route.name = "New Route"

    @api.constrains('from_location_id', 'to_location_id')
    def _validate_route(self):
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

    @onchange('route_level')
    def _onchange_route_level(self):
        for route in self:
            if  route.route_level == constants.RouteLevel.DOMESTIC:
                country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
                if country:
                    country.country_id = country.id

    @api.depends('road_fee', 'trip_salary')
    def _compute_total_cost(self):
        for route in self:
            route.total_cost = route.road_fee + route.trip_salary

    @api.depends('from_location_id.extra_fuel', 'to_location_id.extra_fuel')
    def _compute_extra_fuel(self):
        for route in self:
            route.extra_fuel = route.from_location_id.extra_fuel or route.to_location_id.extra_fuel

    @api.depends('from_location_id', 'to_location_id')
    def _compute_region_id(self):
        for route in self:
            # if route.is_for_sea_freight():
            region_id = None
            if not route.from_location_id.is_local:
                region_id = route.from_location_id.country_id.region_id
            elif not route.to_location_id.is_local:
                region_id = route.to_location_id.country_id.region_id
            route.region_id = region_id

    @api.depends('from_location_id', 'to_location_id')
    def _compute_direction(self):
        for route in self:
            if not route.from_location_id.is_local:
                route.direction = 'import'
            elif not route.to_location_id.is_local or route.to_location_id.type == constants.LocationType.PORT:
                route.direction = 'export'
            else:
                route.direction = 'other'
    @api.depends('from_location_id.country_id', 'to_location_id.country_id')
    def _compute_route_level(self):
        for route in self:
            if route.from_location_id.country_id != route.to_location_id.country_id:
                route.route_level = constants.RouteLevel.INTERNATIONAL
            else:
                route.route_level = constants.RouteLevel.DOMESTIC