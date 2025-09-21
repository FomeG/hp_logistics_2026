from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..services.vehicle_service import VehicleService

class FleetVehicleModelInherit(models.Model):
    _inherit = ['fleet.vehicle.model']

    vehicle_type = fields.Selection([
        ('car', 'Car'),
        ('bike', 'Bike'),
        (VehicleService.VEHICLE_MODEL_TYPE_TRUCK, 'Truck'),
        (VehicleService.VEHICLE_MODEL_TYPE_TRAILER, 'Trailer'),
    ], 
        default=VehicleService.VEHICLE_MODEL_TYPE_TRUCK,
        required=True,
        tracking=True
    )
    
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
