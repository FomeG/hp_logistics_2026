from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ZaloConfirmationWizard(models.TransientModel):
    _name = 'trucking_planning.zalo.confirmation.wizard'
    _description = 'Zalo Message Confirmation Wizard'

    message_content = fields.Text(
        string='Message Content',
        help='Preview of the message that will be sent'
    )
    
    record_id = fields.Integer(
        string='Record ID',
        required=True,
        help='ID of the record to send message for'
    )
    
    record_model = fields.Char(
        string='Record Model',
        required=True,
        help='Model name of the record'
    )
    
    driver_phone = fields.Char(
        string='Driver Phone',
        help='Phone number of the driver (if applicable)'
    )
    
    send_option = fields.Selection([
        ('now', 'Send Now'),
        ('schedule', 'Schedule Later')
    ], string='Send Option', default='now', required=True)
    
    scheduled_date = fields.Datetime(
        string='Scheduled Date & Time',
        help='When to send the message'
    )

    @api.model
    def default_get(self, fields_list):
        """Get default values for the wizard"""
        res = super().default_get(fields_list)
        
        # Get context values
        record_id = self.env.context.get('record_id')
        record_model = self.env.context.get('record_model')
        message_content = self.env.context.get('message_content')
        driver_phone = self.env.context.get('driver_phone')
        bulk_trip_ids = self.env.context.get('bulk_trip_ids')
        
        if record_id and record_model and message_content:
            res.update({
                'record_id': record_id,
                'record_model': record_model,
                'message_content': message_content,
                'driver_phone': driver_phone,
            })
            
            # Store bulk trip IDs in context for later use
            if bulk_trip_ids:
                self = self.with_context(bulk_trip_ids=bulk_trip_ids)
        
        return res

    @api.onchange('send_option')
    def _onchange_send_option(self):
        if self.send_option == 'now':
            self.scheduled_date = False
        elif self.send_option == 'schedule' and not self.scheduled_date:
            # Default to 1 hour from now
            self.scheduled_date = fields.Datetime.now() + timedelta(hours=1)

    def action_send_message(self):
        """Send immediately or schedule for later"""
        if self.send_option == 'now':
            return self._send_immediately()
        else:
            return self._schedule_message()
    
    def _send_immediately(self):
        """Send the message immediately via Zalo API"""
        try:
            # Handle bulk trips case (special case)
            if self.record_model == 'trucking_planning.trip.bulk':
                bulk_trip_ids = self.env.context.get('bulk_trip_ids', [])
                if bulk_trip_ids:
                    trips = self.env['trucking_planning.trip'].browse(bulk_trip_ids)
                    result = self.env['zalo.service'].send_bulk_messages(trips)
                    success_message = f'Messages sent successfully to {len(trips)} trip(s)'
                else:
                    raise UserError("No trips found for bulk sending")
                
                # Return success notification
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Success',
                        'message': success_message,
                        'type': 'success',
                    }
                }
            
            # Get the record for other cases
            record = self.env[self.record_model].browse(self.record_id)
            if not record.exists():
                raise UserError("Record not found")
            
            # Handle different record types
            if self.record_model == 'trucking_planning.trip':
                # Single trip - send directly
                result = self.env['zalo.service'].send_message_with_logging(
                    record, self.message_content, phone=self.driver_phone
                )
                success_message = 'Message sent successfully via Zalo'
                
            elif self.record_model == 'trucking_planning.plan.line':
                # Job - send to all trips using bulk method
                result = self.env['zalo.service'].send_bulk_messages(record.trip_ids)
                success_message = 'Messages sent successfully via Zalo'

            elif self.record_model == 'trucking_planning.plan':
                # Plan - send to all trips
                all_trips = record.mapped('plan_line_ids.trip_ids')
                result = self.env['zalo.service'].send_bulk_messages(all_trips)
                success_message = 'Messages sent successfully via Zalo'

            else:
                # Default case - send directly
                result = self.env['zalo.service'].send_message_with_logging(
                    record, self.message_content, phone=self.driver_phone
                )
                success_message = 'Message sent successfully via Zalo'
            
            # Return success notification
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': success_message,
                    'type': 'success',
                }
            }
            
        except Exception as e:
            raise UserError(f"Failed to send message: {str(e)}")
    
    def _schedule_message(self):
        """Schedule message using queue_job"""
        if not self.scheduled_date:
            raise UserError("Please select a scheduled date and time.")
        
        if self.scheduled_date <= fields.Datetime.now():
            raise UserError("Scheduled date must be in the future.")
        
        # Calculate delay in seconds
        now = fields.Datetime.now()
        delay_seconds = int((self.scheduled_date - now).total_seconds())
        
        # Get bulk trip IDs for bulk case
        bulk_trip_ids = self.env.context.get('bulk_trip_ids', []) if self.record_model == 'trucking_planning.trip.bulk' else []
        
        # Schedule the job using queue_job
        job = self.with_delay(eta=delay_seconds).send_scheduled_message(
            self.record_id,
            self.record_model, 
            self.message_content,
            self.driver_phone,
            bulk_trip_ids
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Message scheduled for {self.scheduled_date.strftime("%Y-%m-%d %H:%M")}. Job ID: {job.uuid}',
                'type': 'success',
            }
        }
    
    def send_scheduled_message(self, record_id, record_model, message_content, driver_phone, bulk_trip_ids=None):
        """Method that will be executed by queue_job at scheduled time"""
        try:
            # Handle bulk trips case (special case)
            if record_model == 'trucking_planning.trip.bulk':
                if bulk_trip_ids:
                    trips = self.env['trucking_planning.trip'].browse(bulk_trip_ids)
                    self.env['zalo.service'].send_bulk_messages(trips)
                    _logger.info(f"Scheduled Zalo messages sent successfully to {len(trips)} trip(s)")
                else:
                    raise UserError("No trips found for bulk sending")
                return
            
            # Get the record for other cases
            record = self.env[record_model].browse(record_id)
            if not record.exists():
                raise UserError("Record not found")
            
            # Send the message using same logic as immediate send
            if record_model == 'trucking_planning.trip':
                self.env['zalo.service'].send_message_with_logging(
                    record, message_content, phone=driver_phone
                )
            elif record_model == 'trucking_planning.plan.line':
                self.env['zalo.service'].send_bulk_messages(record.trip_ids)
            elif record_model == 'trucking_planning.plan':
                all_trips = record.mapped('plan_line_ids.trip_ids')
                self.env['zalo.service'].send_bulk_messages(all_trips)
            else:
                self.env['zalo.service'].send_message_with_logging(
                    record, message_content, phone=driver_phone
                )
                
            # Log success
            _logger.info(f"Scheduled Zalo message sent successfully for {record_model} #{record_id}")
            
        except Exception as e:
            _logger.error(f"Failed to send scheduled Zalo message: {str(e)}")
            raise

    def action_close(self):
        """Close the wizard without sending message"""
        return {'type': 'ir.actions.act_window_close'}
