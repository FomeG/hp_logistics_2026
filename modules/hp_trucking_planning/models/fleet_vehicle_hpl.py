import re
from odoo import models, fields, api
from odoo.exceptions import UserError
from ..services.vehicle_service import VehicleService
from odoo.addons.hp_components.models import constants

class FleetVehicleHpl(models.Model):
    _name = 'fleet.vehicle.hpl'
    _inherits = {'fleet.vehicle': 'vehicle_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

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

    branch_id = fields.Many2one(
        comodel_name='hr.branch',
        index=True,
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
            
            # Create vehicle-driver history if driver is assigned
            if vals.get('driver_id'):
                record.assign_driver()
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
        
        # Create vehicle-driver history if driver is assigned
        if 'driver_id' in vals:
            for record in self:
                if record.driver_id:
                    record.assign_driver()
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

    def assign_driver(self):
        """Create vehicle-driver history record when driver is assigned"""
        vehicle_driver_history_model = self.env['trucking_planning.vehicle.driver.history']
        today = fields.Date.today()
        for vehicle in self:
            driver_partner = vehicle.driver_id
            if not driver_partner:
                continue
                
            # Get the actual fleet.vehicle ID
            fleet_vehicle_id = vehicle.vehicle_id.id if vehicle.vehicle_id else None
            if not fleet_vehicle_id:
                continue
            
            # Find the res.partner.driver record for this res.partner
            driver_record = self.env['res.partner.driver'].search([
                ('partner_id', '=', driver_partner.id)
            ], limit=1)
            
            if not driver_record:
                # If no driver record exists, skip this vehicle
                continue
                
            open_histories = vehicle_driver_history_model.search([
                ('vehicle_id', '=', fleet_vehicle_id),
                ('end_date', '=', False)
            ])
            
            if open_histories:
                if any(h.driver_id == driver_record for h in open_histories):
                    continue
                open_histories.write({'end_date': today})

            vehicle_driver_history_model.create({
                'vehicle_id': fleet_vehicle_id,
                'driver_id': driver_record.id,
                'start_date': today,
            })

    def debug_driver_assignment(self):
        """Debug method to check driver assignment issues"""
        import logging
        _logger = logging.getLogger(__name__)
        
        for vehicle in self:
            _logger.info(f"=== DEBUG Vehicle {vehicle.license_plate} ===")
            _logger.info(f"Driver: {vehicle.driver_id}")
            _logger.info(f"Vehicle ID (hpl): {vehicle.id}")
            _logger.info(f"Vehicle ID (fleet): {vehicle.vehicle_id.id if vehicle.vehicle_id else 'None'}")
            
            if vehicle.driver_id:
                # Check if res.partner.driver exists
                driver_records = self.env['res.partner.driver'].search([
                    ('partner_id', '=', vehicle.driver_id.id)
                ])
                _logger.info(f"Found {len(driver_records)} res.partner.driver records for this partner")
                for dr in driver_records:
                    _logger.info(f"  - Driver record ID: {dr.id}, Name: {dr.name}")
                
                # Check existing history
                if vehicle.vehicle_id:
                    histories = self.env['trucking_planning.vehicle.driver.history'].search([
                        ('vehicle_id', '=', vehicle.vehicle_id.id)
                    ])
                    _logger.info(f"Found {len(histories)} history records for this vehicle")
                    for h in histories:
                        _logger.info(f"  - History ID: {h.id}, Driver: {h.driver_id.name}, Active: {not h.end_date}")

    def create_missing_vehicle_driver_history(self):
        """Create vehicle-driver history records for existing vehicles with drivers but no history"""
        vehicle_driver_history_model = self.env['trucking_planning.vehicle.driver.history']
        today = fields.Date.today()
        
        # Find vehicles with drivers but no active history records
        vehicles_with_drivers = self.search([
            ('driver_id', '!=', False),
            ('id', 'in', self.ids)
        ])
        
        for vehicle in vehicles_with_drivers:
            # Get the actual fleet.vehicle ID
            fleet_vehicle_id = vehicle.vehicle_id.id if vehicle.vehicle_id else None
            if not fleet_vehicle_id:
                continue
            
            # Find the res.partner.driver record for this res.partner
            driver_record = self.env['res.partner.driver'].search([
                ('partner_id', '=', vehicle.driver_id.id)
            ], limit=1)
            
            if not driver_record:
                continue
                
            # Check if there's already an active history record
            existing_history = vehicle_driver_history_model.search([
                ('vehicle_id', '=', fleet_vehicle_id),
                ('end_date', '=', False)
            ])
            
            if not existing_history:
                # Create history record
                vehicle_driver_history_model.create({
                    'vehicle_id': fleet_vehicle_id,
                    'driver_id': driver_record.id,
                    'start_date': today,
                })

    @api.model
    def create_all_missing_vehicle_driver_history(self):
        """Create vehicle-driver history records for ALL existing vehicles with drivers but no history"""
        vehicle_driver_history_model = self.env['trucking_planning.vehicle.driver.history']
        today = fields.Date.today()
        
        # Find ALL vehicles with drivers but no active history records
        vehicles_with_drivers = self.search([
            ('driver_id', '!=', False)
        ])
        
        created_count = 0
        for vehicle in vehicles_with_drivers:
            # Get the actual fleet.vehicle ID
            fleet_vehicle_id = vehicle.vehicle_id.id if vehicle.vehicle_id else None
            if not fleet_vehicle_id:
                continue
            
            # Find the res.partner.driver record for this res.partner
            driver_record = self.env['res.partner.driver'].search([
                ('partner_id', '=', vehicle.driver_id.id)
            ], limit=1)
            
            if not driver_record:
                continue
                
            # Check if there's already an active history record
            existing_history = vehicle_driver_history_model.search([
                ('vehicle_id', '=', fleet_vehicle_id),
                ('end_date', '=', False)
            ])
            
            if not existing_history:
                # Create history record
                vehicle_driver_history_model.create({
                    'vehicle_id': fleet_vehicle_id,
                    'driver_id': driver_record.id,
                    'start_date': today,
                })
                created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Created {created_count} vehicle-driver history records',
                'sticky': False,
            }
        }