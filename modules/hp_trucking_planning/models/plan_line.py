from odoo import models, api, fields


class PlanLine(models.Model):
    _name = 'trucking_planning.plan.line'
    _description = 'Plan Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date asc'

    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        string='Plan',
        required=True,
    )
    code = fields.Char(
        string='Job Number',
        required=True,
        tracking=True,
    )
    date = fields.Date(
        required=True,
        related='plan_id.date',
        readonly=True,
        string='Return Shipment Date',
        tracking=True,
    )
    status = fields.Selection([
            ('hpl_reject','HPL Reject'),
            ('client_cancel','Client Cancel'),
            ('checking','Checking'),
            ('transfer','Transfer'),
            ('rented','Rented')
        ],
        string='Status',
        required=True,
        tracking=True,
    )
    client_id = fields.Many2one(
        comodel_name='trucking_planning.client',
        required=True,
        inverse_name='plan_line_ids',
    )
    tax_number = fields.Char(
        related='client_id.tax_number',
        readonly=True,
        string='Tax number',
        store=True,
        tracking=True,
    )
    booking = fields.Char(
        string="Booking",
        required=True,
        tracking=True,
    )
    container_number = fields.Char(
        string="Container Number",
        required=True,
        tracking=True,
    )
    seal_number = fields.Char(
        string="Seal Number",
        required=True,
        tracking=True,
    )
    container_type = fields.Selection([
        ('dry','Dry'),
        ('cool','Cool'),
        ('ot','OT'),
        ('ft','FT')
    ], string="Container Type", required=True, tracking=True)

    container_size = fields.Selection([
        ('20','20'),
        ('40','40')
    ], string="Container Size", required=True, tracking=True)
    shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
        required=True,
    )
    plan_type = fields.Selection([
        ('export','Export'),
        ('import','Import'),
    ], string="Plan Type", required=True, tracking=True)

    route_id = fields.Many2one(
        comodel_name='trucking_planning.route', required=True
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string='From Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string = 'To Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    container_pickup = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    goods_pickup_delivery = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    contact_phone = fields.Char(
        string="Contact Phone",
        related='goods_pickup_delivery.contact_phone',
    )
    container_delivery = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain=[('type','=','truck')],
        related='plan_id.vehicle_id',
        readonly=True,
        store=True,
    )
    driver_id = fields.Many2one(
        comodel_name="trucking_planning.driver",
        default=lambda self: self._get_default_driver(),
        domain="[('active', '=', True)]",
        index=True,
    )
    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain=[('type', '=', 'trailer')],
        related='plan_id.vehicle_id.trailer_id',
        readonly=True,
        store=True,
    )
    is_rented = fields.Boolean(
        related='truck_id.is_rented',
        string="Is Rented",
        tracking=True,
    )
    contract_number = fields.Char(
        string="Contact Number",
        tracking=True,
    )
    note = fields.Text(string="Note")
    weight_class = fields.Selection([
        ('inferior_20', '<20T'),
        ('superior_20', '>20T'),
        ('mix', 'Mix')
    ],
        required=True,
        string="Weight Class",
        tracking=True,
    )
    extra_charge = fields.Float(string="Extra Charge", tracking=True)
    extra_fuel = fields.Float(string="Extra Fuel", tracking=True)
    fuel_liters = fields.Float(
        compute='_compute_fuel_liters',
        store=True,
        string="Fuel Liters",
        tracking=True,
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute='_compute_total_cost',
        store=True,
        readonly=True,
        tracking=True,
    )
    _sql_constraints = [
        ('unique_booking','Unique(booking)','Booking number is unique!'),
    ]

    @api.depends('plan_type', 'route_id')
    def _compute_actual_locations(self):
        for rec in self:
            if rec.route_id:
                if rec.plan_type == 'export':
                    rec.actual_source_location_id = rec.route_id.from_location_id
                    rec.actual_destination_location_id = rec.route_id.to_location_id
                else:  # import
                    rec.actual_source_location_id = rec.route_id.to_location_id
                    rec.actual_destination_location_id = rec.route_id.from_location_id
            else:
                rec.actual_source_location_id = False
                rec.actual_destination_location_id = False

    @api.depends('route_id', 'truck_id', 'weight_class','extra_fuel')
    def _compute_fuel_liters(self):
        for rec in self:
            if rec.route_id and rec.truck_id:
                fuel_rate = rec.truck_id.fuel_rate_mix
                if rec.weight_class == 'inferior_20':
                    fuel_rate = rec.truck_id.fuel_rate_inferior_20
                elif rec.weight_class == 'superior_20':
                    fuel_rate = rec.truck_id.fuel_rate_superior_20
                distance = rec.route_id.distance_km
                if rec.route_id.extra_fuel:
                    distance = rec.route_id.distance_km + 40
                rec.fuel_liters = distance * fuel_rate * 2 + rec.extra_fuel
            else:
                rec.fuel_liters = 0.0

    @api.depends('route_id','extra_charge')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = rec.route_id.total_cost + rec.extra_charge

    @api.model
    def _get_default_driver(self):
        plan_id = self.env.context.get('default_plan_id')
        if plan_id:
            plan = self.env['trucking_planning.plan'].browse(plan_id)
            if plan.vehicle_id and plan.vehicle_id.primary_driver_id:
                return plan.vehicle_id.primary_driver_id.id
        return False

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id and self.plan_id.vehicle_id and self._origin.plan_id != self.plan_id:
            self.driver_id = self.plan_id.vehicle_id.primary_driver_id