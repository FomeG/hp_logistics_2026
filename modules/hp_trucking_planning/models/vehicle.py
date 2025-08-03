from email.policy import default

from odoo import models, fields, api


class Vehicle(models.Model):
    _name = 'trucking_planning.vehicle'
    _description = 'Trucking Planning Vehicle'
    _inherit = ['unique.normalized.name.mixin']

    type = fields.Selection([
        ('truck', 'Truck'),
        ('trailer', 'Trailer'),
    ], default='truck')
    name = fields.Char(
        string='Số xe',
        required=True,
    )
    #applied only for truck
    engine_type = fields.Selection([
        ('small','Small'),
        ('big','Big'),
    ],default='small')
    fuel_rate_inferior_20 = fields.Float(
        compute='_compute_fuel_rate_inferior_20',
        default=0.0,
        store=True,
    )
    fuel_rate_superior_20 = fields.Float(
        compute='_compute_fuel_rate_superior_20',
        default=0.0,
        store=True,
    )
    fuel_rate_mix = fields.Float(
        compute='_compute_fuel_rate_mix',
        default=0.0,
        store=True,
    )
    registration_date = fields.Date(
        string='Registration Date',
    )
    is_rented = fields.Boolean(
        string='Is rented',
        default=False,
    )
    @api.depends('type')
    def _compute_fuel_rate_inferior_20(self):
        for vehicle in self:
            vehicle.fuel_rate_inferior_20 = 0.0
            if vehicle.type == 'truck':
                vehicle.fuel_rate_inferior_20 = 0.35
                if  vehicle.engine_type == 'small':
                    vehicle.fuel_rate_inferior_20 = 0.32
    @api.depends('type')
    def _compute_fuel_rate_superior_20(self):
        for vehicle in self:
            vehicle.fuel_rate_superior_20 = 0.0
            if vehicle.type == 'truck':
                vehicle.fuel_rate_superior_20 = 0.38
                if  vehicle.engine_type == 'small':
                    vehicle.fuel_rate_superior_20 = 0.35
    @api.depends('type')
    def _compute_fuel_rate_mix(self):
        for vehicle in self:
            vehicle.fuel_rate_mix = 0.0
            if vehicle.type == 'truck':
                vehicle.fuel_rate_mix = 0.42
                if  vehicle.engine_type == 'small':
                    vehicle.fuel_rate_mix = 0.38
