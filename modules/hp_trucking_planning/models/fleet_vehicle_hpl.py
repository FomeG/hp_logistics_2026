import re
from odoo import models, fields, api
from odoo.exceptions import UserError
from ..services.vehicle_service import VehicleService
from odoo.addons.hp_components.models import constants

class FleetVehicleHpl(models.Model):
    _name = 'fleet.vehicle.hpl'
    _inherits = {'fleet.vehicle': 'vehicle_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HPL Fleet Vehicle'

    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Vehicle',
        required=True,
        ondelete='cascade',
        index=True,
    )
    trailer_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Trailer',
        domain=lambda self: self._get_trailer_domain(),
        index=True,
    )
    fuel_rate_inferior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Light',
        tracking=True,
        store=True,
    )
    fuel_rate_superior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Heavy',
        tracking=True,
        store=True,
    )
    fuel_rate_mix = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Mix',
        tracking=True,
        store=True,
    )
    fake_category_type = fields.Selection([
        (constants.VehicleModelCategory.TRUCK, 'Truck'),
        (constants.VehicleModelCategory.TRAILER, 'Trailer'),
        ],
        default=lambda self: self._get_vehicle_type(),
        required=True,
        string="Type",
        store=False,
    )

    fake_engine_type = fields.Selection([
        (constants.VehicleEngineType.SMALL,'Small'),
        (constants.VehicleEngineType.BIG, 'Big'),
        ],default=lambda self: self._get_engine_type(),
            string="Engine Type",
            store=False,
            required=True,
    )

    is_trailer = fields.Boolean(
        compute='_compute_is_trailer',
        store=False,
    )

    _sql_constraints = [
        ('unique_trailer_assignment', 'unique(trailer_id)', 'This trailer is already assigned to another vehicle.'),
    ]

    @api.depends('model_id', 'tag_ids')
    def _compute_fuel_rates(self):
        vehicle_service = VehicleService(self.env)
        for vehicle in self:
            if not vehicle_service.is_truck(vehicle):
                vehicle.fuel_rate_inferior_20 = 0.0
                vehicle.fuel_rate_superior_20 = 0.0
                vehicle.fuel_rate_mix = 0.0
                continue

            if vehicle_service.is_small_engine(vehicle):
                vehicle.fuel_rate_inferior_20 = 0.32
                vehicle.fuel_rate_superior_20 = 0.35
                vehicle.fuel_rate_mix = 0.38
            elif vehicle_service.is_big_engine(vehicle):
                vehicle.fuel_rate_inferior_20 = 0.35
                vehicle.fuel_rate_superior_20 = 0.38
                vehicle.fuel_rate_mix = 0.42
            else:
                vehicle.fuel_rate_inferior_20 = 0.0
                vehicle.fuel_rate_superior_20 = 0.0
                vehicle.fuel_rate_mix = 0.0

    @api.model
    def _get_trailer_domain(self):
        vehicle_service = VehicleService(self.env)
        trailer_category = vehicle_service._get_or_create_vehicle_model_category_by_name(constants.VehicleModelCategory.TRAILER)
        assigned_trailer_ids = self.search([
            ('trailer_id', '!=', False)
        ]).mapped('trailer_id.id')
        return [
            ('active', '=', True),
            ('category_id', '=', trailer_category.id),
            ('id', 'not in', assigned_trailer_ids)
        ]

    @api.model_create_multi
    def create(self, vals_list):
        vehicle_service = VehicleService(self.env)
        records = self.env['fleet.vehicle.hpl']
        for vals in vals_list:
            if not vals.get('fake_category_type') or not vals.get('fake_engine_type'):
                raise UserError("Vehicle must have category information")
            if vals.get('license_plate'):
                vals['license_plate'] = self._clean_license_plate(vals['license_plate'])

            # Initialize vehicle data based on type
            hpl_data = vehicle_service.init_hpl_data_by_type(vals.get('fake_category_type'))
            vals.update(hpl_data)

            # Create the HPL record
            record = super(FleetVehicleHpl, self).create(vals)
            records += record
            if vals.get('fake_engine_type') == constants.VehicleEngineType.BIG:
                vehicle_service.set_big_engine(record)
            else:
                vehicle_service.set_small_engine(record)

        return records

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = self._clean_license_plate(vals['name'])
        result = super().write(vals)
        if 'fake_engine_type' in vals:
            vehicle_service = VehicleService(self.env)
            for record in self:
                if vals['fake_engine_type'] == constants.VehicleEngineType.BIG:
                    vehicle_service.set_big_engine(record)
                else:
                    vehicle_service.set_small_engine(record)

        return result

    def _clean_license_plate(self, plate):
        return re.sub(r'[^A-Za-z0-9-]', '', plate)

    def _compute_is_trailer(self):
        vehicle_service = VehicleService(self.env)
        for record in self:
            record.is_trailer = vehicle_service.is_trailer(record)

    def _get_engine_type(self):
        vehicle_service = VehicleService(self.env)
        for record in self:
            if vehicle_service.is_small_engine(record):
                return constants.VehicleEngineType.SMALL
        return constants.VehicleEngineType.BIG

    def _get_vehicle_type(self):
        vehicle_service = VehicleService(self.env)
        for record in self:
            if vehicle_service.is_trailer(record):
                return constants.VehicleModelCategory.TRAILER
        return constants.VehicleModelCategory.TRUCK
