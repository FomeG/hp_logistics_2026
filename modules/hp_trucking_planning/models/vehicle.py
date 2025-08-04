from odoo import models, fields, api


class Vehicle(models.Model):
    _name = 'trucking_planning.vehicle'
    _description = 'Trucking Planning Vehicle'
    _inherit = ['unique.normalized.name.mixin']

    type = fields.Selection([
        ('truck', 'Truck'),
        ('trailer', 'Trailer'),
    ],
        default='truck',
        index=True,
        required=True
    )
    name = fields.Char(
        string='Số xe',
        required=True,
    )
    engine_type = fields.Selection([
        ('small','Small'),
        ('big','Big'),
    ],default='small')

    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        string='Trailer',
        domain=[
            ('active', '=', True),
            ('type','=','trailer'),
        ],
        index=True,
    )

    primary_driver_id = fields.Many2one(
        comodel_name='trucking_planning.driver',
        domain="[('active', '=', True)]",
        index=True,
    )
    fuel_rate_inferior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=3.2,
        store=True,
        string='Light',
    )
    fuel_rate_superior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=3.5,
        store=True,
        string='Heavy',
    )
    fuel_rate_mix = fields.Float(
        compute='_compute_fuel_rates',
        default=3.8,
        store=True,
        string='Mix',
    )
    registration_date = fields.Date(
        string='Registration Date',
    )
    is_rented = fields.Boolean(
        string='Is rented',
        default=False,
    )
    active = fields.Boolean(
        default=True,
    )
    plan_ids = fields.One2many(
        comodel_name='trucking_planning.plan',
        string='Plans',
        inverse_name='vehicle_id',
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        string='Trips',
        inverse_name='truck_id',
    )
    vehicle_driver_history_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle.driver.history',
        inverse_name='vehicle_id',
    )

    @api.depends('type', 'engine_type')
    def _compute_fuel_rates(self):
        for vehicle in self:
            if vehicle.type != 'truck':
                vehicle.fuel_rate_inferior_20 = 0.0
                vehicle.fuel_rate_superior_20 = 0.0
                vehicle.fuel_rate_mix = 0.0
                continue

            if vehicle.engine_type == 'small':
                vehicle.fuel_rate_inferior_20 = 3.2
                vehicle.fuel_rate_superior_20 = 3.5
                vehicle.fuel_rate_mix = 3.8
            else:  # big engine
                vehicle.fuel_rate_inferior_20 = 3.5
                vehicle.fuel_rate_superior_20 = 3.8
                vehicle.fuel_rate_mix = 4.2
