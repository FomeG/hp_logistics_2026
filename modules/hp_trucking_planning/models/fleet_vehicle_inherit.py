from odoo import models, fields, api
from ..services.vehicle_service import VehicleService
from ..services.res_partner_service import ResPartnerService
import re

class FleetVehicleInherit(models.Model):
    _inherit = ['fleet.vehicle']

    model_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string='Model',
        tracking=True,
        required=True,
        default=lambda self: self._get_default_model(),
    )
    engine_type = fields.Selection([
        (VehicleService.VEHICLE_ENGINE_TYPE_SMALL, 'Small'),
        (VehicleService.VEHICLE_ENGINE_TYPE_BIG, 'Big'),
    ],
        default=VehicleService.VEHICLE_ENGINE_TYPE_SMALL,
        string="Engine Type",
        tracking=True
    )
    trailer_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string='Trailer',
        domain=lambda self: self._get_trailer_domain(),
        index=True,
    )
    driver_id = fields.Many2one(
        comodel_name='res.partner.driver',
        domain=[('type','=', ResPartnerService.PARTNER_TYPE_DRIVER)],
        index=True,
    )
    fuel_rate_inferior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Light',
        tracking=True,
    )
    fuel_rate_superior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Heavy',
        tracking=True,
    )
    fuel_rate_mix = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        string='Mix',
        tracking=True,
    )
    is_rented = fields.Boolean(
        string='Is rented',
        default=False,
        tracking=True,
    )
    vehicle_driver_history_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle.driver.history',
        inverse_name='vehicle_id',
    )
    trucking_branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        default=lambda self: self._get_default_branch(),
    )

    _sql_constraints = [
        ('unique_trailer_assignment', 'unique(trailer_id)', 'This trailer is already assigned to another vehicle.'),
    ]

    def _compute_display_name(self):
        for record in self:
            record.display_name = record.license_plate

    @api.depends('model_id', 'engine_type')
    def _compute_fuel_rates(self):
        for vehicle in self:
            if vehicle.vehicle_type != VehicleService.VEHICLE_MODEL_TYPE_TRUCK:
                vehicle.fuel_rate_inferior_20 = 0.0
                vehicle.fuel_rate_superior_20 = 0.0
                vehicle.fuel_rate_mix = 0.0
                continue

            if vehicle.engine_type == VehicleService.VEHICLE_ENGINE_TYPE_SMALL:
                vehicle.fuel_rate_inferior_20 = 0.32
                vehicle.fuel_rate_superior_20 = 0.35
                vehicle.fuel_rate_mix = 0.38
            else:  # big engine
                vehicle.fuel_rate_inferior_20 = 0.35
                vehicle.fuel_rate_superior_20 = 0.38
                vehicle.fuel_rate_mix = 0.42

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = self._clean_license_plate(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = self._clean_license_plate(vals['name'])
        return super().write(vals)

    def _clean_license_plate(self, plate):
        return re.sub(r'[^A-Za-z0-9-]', '', plate)
    
    @api.model
    def _get_default_branch(self):
        return self.env['trucking_planning.branch'].sudo().search([('user_ids', 'in', [self.env.uid])], limit=1)

    @api.model
    def _get_default_model(self):
        return self.env['fleet.vehicle.model'].sudo().search([('vehicle_type', '=', VehicleService.VEHICLE_MODEL_TYPE_TRUCK)], limit=1)
    
    @api.model
    def _get_trailer_domain(self):
        assigned_trailer_ids = self.search([
            ('trailer_id', '!=', False)
        ]).mapped('trailer_id.id')

        return [
            ('active', '=', True),
            ('vehicle_type', '=', VehicleService.VEHICLE_MODEL_TYPE_TRAILER),
            ('id', 'not in', assigned_trailer_ids)
        ]
    
    def assign_driver(self):
        vehicle_driver_history_model = self.env['trucking_planning.vehicle.driver.history']
        today = fields.Date.today()
        for vehicle in self:
            driver = vehicle.driver_id
            if not driver:
                continue
            open_histories = vehicle_driver_history_model.search([
                ('vehicle_id', '=', vehicle.id),
                ('end_date', '=', False)
            ])
            if open_histories:
                if any(h.driver_id == driver for h in open_histories):
                    continue
                open_histories.write({'end_date': today})

            vehicle_driver_history_model.create({
                'vehicle_id': vehicle.id,
                'driver_id': driver.id,
                'start_date': today,
            })