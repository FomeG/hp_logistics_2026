from odoo import models, fields, api

class CsOrderBase(models.AbstractModel):
    _name = 'cs.order.base'
    _description = 'CS Order Base'

    location_id = fields.Many2one(
        comodel_name='location.base',
        string="Port Pickup/Drop",
        tracking=True,
        domain=[('type', '=', 'port')],
        help="Export: Port to pickup full container\nImport: Port to drop off full container",
        index=True,
        required=True,
    )

    container_port_location_id = fields.Many2one(
        comodel_name='location.base',
        string="Empty Container Depot",
        domain=[('type', '=', 'depot')],
        tracking=True,
        required=True,
        help="Depot where empty container is picked up (Export) or returned (Import)"
    )

    goods_pickup_location_id = fields.Many2one(
        comodel_name='location.base',
        string="Goods Pickup Location",
        tracking=True,
        domain=[('type', '=', 'goods_pickup_delivery')],
        index=True,
        required=True,
    )

    goods_delivery_location_id = fields.Many2one(
        comodel_name='location.base',
        string="Goods Delivery Location",
        tracking=True,
        domain=[('type', '=', 'goods_pickup_delivery')],
        help="Import: Location to deliver goods to consignee\nExport: Not used for CY-CY",
        index=True,
        required=True,
    )

    date = fields.Datetime(
        string="Load/Return Date",
        tracking=True,
        help="Export: Container loading date at port\nImport: Empty container return date at depot",
        index=True,
        required=True,
    )

    estimate_time_departure = fields.Datetime(
        string="ETD",
        tracking=True,
        help="Estimated Time of Departure",
        index=True,
        required=True,
    )

    estimate_time_arrival = fields.Datetime(
        string="ETA",
        tracking=True,
        help="Estimated Time of Arrival",
        index=True,
        required=True,
    )

    #route fields
    route_id = fields.Many2one(
        comodel_name='route.base',
        string='Route',
        tracking=True,
        index=True,
        required=True,
    )

    actual_source_location_id = fields.Many2one(
        comodel_name='location.base',
        compute='_compute_actual_locations',
        string='From Location',
        store=True,
        readonly=True,
        tracking=True,
        required=True,
    )

    actual_destination_location_id = fields.Many2one(
        comodel_name='location.base',
        compute='_compute_actual_locations',
        string='To Location',
        store=True,
        readonly=True,
        tracking=True,
        required=True,
    )

    route_direction = fields.Selection(
        related='route_id.direction',
        string='Direction',
        store=False,
        readonly=True,
        required=True,
    )

    @api.depends('route_id', 'route_id.from_location_id', 'route_id.to_location_id', 'route_id.direction')
    def _compute_actual_locations(self):
        for rec in self:
            if rec.route_id:
                rec.actual_source_location_id = rec.route_id.from_location_id
                rec.actual_destination_location_id = rec.route_id.to_location_id
            else:
                rec.actual_source_location_id = False
                rec.actual_destination_location_id = False