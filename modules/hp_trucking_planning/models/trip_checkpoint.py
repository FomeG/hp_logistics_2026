from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class TripCheckpoint(models.Model):
    _name = 'trucking_planning.trip_checkpoint'
    _description = 'Trip Checkpoint'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    trip_id = fields.Many2one(
        comodel_name='trucking_planning.trip',
        string='Trip',
        required=True,
        index=True,
        ondelete='cascade'
    )
    
    longitude = fields.Float(
        string='Longitude',
        required=True,
        digits=(10, 7),
        help='Longitude coordinate (-180 to 180)'
    )
    
    latitude = fields.Float(
        string='Latitude',
        required=True,
        digits=(10, 7),
        help='Latitude coordinate (-90 to 90)'
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('trip_id', 'latitude', 'longitude')
    def _compute_display_name(self):
        for record in self:
            if record.trip_id:
                trip_name = record.trip_id.code or f"Trip {record.trip_id.id}"
                record.display_name = f"{trip_name} - {record.latitude}, {record.longitude}"
            else:
                record.display_name = f"Checkpoint {record.id}"

    @api.constrains('longitude')
    def _check_longitude(self):
        for record in self:
            if not -180 <= record.longitude <= 180:
                raise ValidationError('Longitude must be between -180 and 180 degrees.')

    @api.constrains('latitude')
    def _check_latitude(self):
        for record in self:
            if not -90 <= record.latitude <= 90:
                raise ValidationError('Latitude must be between -90 and 90 degrees.')

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to validate data and log creation"""
        records = super().create(vals_list)
        
        # Log checkpoint creation for audit
        for record in records:
            _logger.info(
                f"GPS Checkpoint created: Trip {record.trip_id.id}, "
                f"Location: {record.latitude}, {record.longitude}"
            )
            
            # Post message to trip chatter
            if record.trip_id:
                record.trip_id.message_post(
                    body=f"GPS location received: {record.latitude}, {record.longitude}",
                    message_type='notification',
                    subtype_xmlid='mail.mt_note'
                )
        
        return records

    def get_google_maps_url(self):
        """Generate Google Maps URL for this location"""
        self.ensure_one()
        return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"

    def action_view_on_map(self):
        """Open location in Google Maps"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_google_maps_url(),
            'target': 'new',
        }

