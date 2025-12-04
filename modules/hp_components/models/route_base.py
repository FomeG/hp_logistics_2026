from odoo import models, fields, api, _
from odoo.api import onchange, ValuesType, Self
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
        default=constants.TransportMode.TRUCK,
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

    @api.constrains('from_location_id', 'to_location_id','transport_mode')
    def _validate_route(self):
        for route in self:
            if route.from_location_id == route.to_location_id:
                raise ValidationError("Origin and destination must be different.")
            if route.transport_mode == constants.TransportMode.TRUCK:
                existing_route = self.search([
                    ('id', '!=', route.id),
                    ('transport_mode', '=', constants.TransportMode.TRUCK),
                    '|',
                    '&', ('from_location_id', '=', route.from_location_id.id),
                    ('to_location_id', '=', route.to_location_id.id),
                    '&', ('from_location_id', '=', route.to_location_id.id),
                    ('to_location_id', '=', route.from_location_id.id),
                ])
            else:
                existing_route = self.search([
                    ('id', '!=', route.id),
                    ('transport_mode', '=', route.transport_mode),
                    '&', ('from_location_id', '=', route.from_location_id.id),
                    ('to_location_id', '=', route.to_location_id.id),
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
            return route.transport_mode == constants.TransportMode.SEA

    def is_for_truck_freight(self):
        for route in self:
            return route.transport_mode == constants.TransportMode.TRUCK

    @api.model
    def create_freight_sea_from_port(self, location_base):
        vals_list = []
        if location_base.is_local:
            ports = self.env['hp_components.geo.service'].get_international_ports()
            for port in ports:
                vals_list.append({
                    'from_location_id': location_base.id,
                    'to_location_id': port.id,
                    'transport_mode': constants.TransportMode.SEA,
                })
        else:
            ports = self.env['hp_components.geo.service'].get_local_ports()
            for port in ports:
                vals_list.append({
                    'from_location_id': port.id,
                    'to_location_id': location_base.id,
                    'transport_mode': constants.TransportMode.SEA,
                })

        if len(vals_list) > 0:
            super().create(vals_list)

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        LocationBase = self.env['location.base']
        for vals in vals_list:
            if vals.get('from_location_id') and vals.get('to_location_id'):
                fr = LocationBase.browse(vals['from_location_id'])
                to = LocationBase.browse(vals['to_location_id'])
                if fr and to and fr.is_local and to.is_local:
                    vals['transport_mode'] = constants.TransportMode.TRUCK
        return super().create(vals_list)

    def write(self, vals):
        LocationBase = self.env['location.base']
        for route in self:
            if 'from_location_id' in vals or 'to_location_id' in vals:
                from_loc = route.from_location_id
                to_loc = route.to_location_id
                is_local = True
                if 'from_location_id' in vals:
                    from_loc = LocationBase.browse(vals['from_location_id'])
                if 'to_location_id' in vals:
                    to_loc = LocationBase.browse(vals['to_location_id'])

                if not to_loc.is_local or not from_loc.is_local:
                    is_local = False
                vals['transport_mode'] = constants.TransportMode.SEA
                if is_local:
                    vals['transport_mode'] = constants.TransportMode.TRUCK
        return super().write(vals)

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