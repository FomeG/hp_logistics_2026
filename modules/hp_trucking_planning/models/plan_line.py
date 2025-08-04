from odoo import models, api, fields


class PlanLine(models.Model):
    _name = 'trucking_planning.plan.line'
    _description = 'Plan Line'
    _order = 'date asc'
    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        string='Plan',
        required=True,
    )
    code = fields.Char(
        string='Job number',
        required=True
    )
    date = fields.Date(
        required=True,
        related='plan_id.date',
        readonly=True,
        string='Ngày đóng trả hàng',
    )
    status = fields.Selection([
        ('hpl_reject','HPL từ chối'),
        ('client_cancel','KH huỷ'),
        ('checking','Đang kiểm tra thông tin'),
        ('transfer','Chuyển điều động'),
        ('rented','Thuê ngoài')
        ],
        string='Status'
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
    )
    booking = fields.Char(
        required=True,
    )
    container_number = fields.Char(
        required=True,
    )
    seal_number = fields.Char(
        required=True,
    )
    container_type = fields.Selection([
        ('dry','Khô'),
        ('cool','Lạnh'),
        ('ot','OT'),
        ('FT','ft')
    ],required=True)

    container_size = fields.Selection([
        ('20','20'),
        ('40','40')
    ],required=True)
    shipping_line_id = fields.Many2one(
        comodel_name='trucking_planning.shipping_line',
        required=True,
    )
    plan_type = fields.Selection([
        ('export','Export'),
        ('import','Import'),
    ],required=True)

    route_id = fields.Many2one(
        comodel_name='trucking_planning.route', required=True
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string='From Location',
        store=True,
        readonly=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string = 'To Location',
        store=True,
        readonly=True,
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
        related='goods_pickup_delivery.contact_phone',
    )
    container_delivery = fields.Many2one(
        comodel_name="trucking_planning.location",
        required=True,
    )
    driver_id = fields.Many2one(
        comodel_name="trucking_planning.driver",
        related='plan_id.vehicle_id.primary_driver_id',
    )
    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain=[('type','=','truck')],
        related='plan_id.vehicle_id',
        readonly=True,
        store=True,
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
        string="Is Rented"
    )
    contract_number = fields.Char()
    note = fields.Text()
    weight_class = fields.Selection([
        ('inferior_20', '<20T'),
        ('superior_20', '>20T'),
        ('mix', 'Mix')
    ],
        required=True,
    )
    fuel_liters = fields.Float(
        compute='_compute_fuel_liters',
        store=True,
        string="Số lít dầu"
    )
    plan_total_cost = fields.Float(
        related='route_id.total_cost',
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

    @api.depends('route_id', 'truck_id', 'weight_class')
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
                rec.fuel_liters = distance * fuel_rate * 2
            else:
                rec.fuel_liters = 0.0
