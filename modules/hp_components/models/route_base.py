from odoo import models, fields, api, _
from odoo.api import onchange
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

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
    transport_mode = fields.Selection(
        constants.TransportMode.SELECT_OPTIONS,
        required=True,
        default=constants.TransportMode.SEA,
        tracking=True,
    )
    route_level = fields.Selection(
        constants.RouteLevel.SELECT_OPTIONS,
        default=constants.RouteLevel.INTERNATIONAL,
        tracking=True,
        required=True,
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        string='From Location',
        tracking=True,
        index=True,
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
    ], default='export', string='Direction', tracking=True)

    distance_km = fields.Float(
        required=False,
        string='Distance KM',
        tracking=True,
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


    @api.depends('from_location_id', 'to_location_id')
    def _compute_name(self):
        for route in self:
            if route.from_location_id and route.to_location_id:
                route.name = f"{route.from_location_id.name} -> {route.to_location_id.name}"
            else:
                route.name = "New Route"


    @api.constrains('from_location_id', 'to_location_id','transport_mode')
    def _validate_route(self):
        for route in self:
            ft = route.from_location_id.type
            tt = route.to_location_id.type
            mode = route.transport_mode
            allowed = {}
            def invalid():
                raise ValidationError(_('From/To location types are not compatible with transport mode %s') % dict(route._fields['transport_mode'].selection).get(mode))

            if mode == constants.TransportMode.SEA:
                allowed = constants.LocationType.TYPES_4_SEA_ROUTE
            elif mode == constants.TransportMode.TRUCK:
                allowed = constants.LocationType.TYPES_4_TRUCK_ROUTE

            if ft not in allowed or tt not in allowed:
                invalid()

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

    @onchange('transport_mode')
    def _onchange_transport_mode(self):
        for route in self:
            if  route.transport_mode == constants.TransportMode.TRUCK:
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

    def is_for_sea_freight(self):
        for route in self:
            if route.transport_mode == constants.TransportMode.SEA:
                return True
        return False

    def is_for_truck_freight(self):
        for route in self:
            if route.transport_mode == constants.TransportMode.TRUCK:
                return True
        return False