from odoo import models, api, tools
from odoo.exceptions import UserError
import requests
import logging

_logger = logging.getLogger(__name__)


class ZaloService(models.AbstractModel):
    _name = 'zalo.service'
    _description = 'Zalo Message Service'

    # Default configuration values
    DEFAULT_PHONE = '84'
    DEFAULT_WEBSITE_ID = '1'

    def _get_api_url(self):
        """Get the Zalo API URL from Odoo configuration"""
        try:
            # Get the API URL from Odoo configuration
            api_url = tools.config['zalo_message_api_url']
            if not api_url:
                raise UserError("Zalo API URL is not configured. Please add 'zalo_message_api_url' to your odoo.conf file.")
            return api_url
        except Exception as e:
            if isinstance(e, UserError):
                raise e
            _logger.error(f"Error getting Zalo API URL from config: {str(e)}")
            raise UserError("Failed to get Zalo API URL from configuration. Please check your odoo.conf file.")

    def send_message(self, message_content, phone=None, website_id=None):

        try:
            import requests
        except ImportError:
            raise UserError("requests library is required. Please install it using: pip install requests")
        
        # Use default values if not provided
        phone = phone or self.DEFAULT_PHONE
        website_id = website_id or self.DEFAULT_WEBSITE_ID
        
        # Get API URL from configuration
        api_url = self._get_api_url()
        
        # API parameters
        params = {
            'phone': phone,
            'message': message_content,
            'website_id': website_id
        }
        
        try:
            response = requests.post(api_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json() if response.text else {'status': 'success'}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to send message: {str(e)}"
            raise UserError(error_msg)

    def send_message_with_logging(self, record, message_content, phone=None, website_id=None):

        try:
            # Send the message
            response = self.send_message(message_content, phone, website_id)
            
            # Log success to the record
            phone_info = f"Phone: {phone}" if phone else "Phone: Default"
            record.message_post(
                body=f"✅ Message sent successfully via Zalo API\n"
                     f"{phone_info}\n"
                     f"Content: {message_content[:2000]}{'...' if len(message_content) > 2000 else ''}\n"
                     f"Response: {response}",
                message_type='notification'
            )
            
            return response
            
        except Exception as e:
            # Log error to the record
            phone_info = f"Phone: {phone}" if phone else "Phone: Default"
            record.message_post(
                body=f"❌ Failed to send message via Zalo API\n"
                     f"{phone_info}\n"
                     f"Error: {str(e)}\n"
                     f"Content: {message_content[:100]}{'...' if len(message_content) > 100 else ''}",
                message_type='notification'
            )
            raise

    def send_bulk_messages(self, records):

        success_count = 0
        failed_count = 0
        failed_records = []
        
        for record in records:
            try:
                # Build message content for this record
                if hasattr(record, '_build_message_content'):
                    message_content = record._build_message_content()
                else:
                    raise UserError(f"Record {record._name} does not have _build_message_content method")
                
                # Get driver phone number for trip records
                driver_phone = None
                if hasattr(record, 'driver_id') and record.driver_id and record.driver_id.phone_number:
                    driver_phone = record.driver_id.phone_number
                
                # Send message
                self.send_message_with_logging(record, message_content, phone=driver_phone)
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_records.append({
                    'record': record,
                    'error': str(e)
                })
                _logger.error(f"Failed to send message to {record._name} {record.id}: {str(e)}")
        
        # Show summary notification
        if success_count > 0 and failed_count == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': f'Successfully sent messages to {success_count} record(s)',
                    'type': 'success',
                }
            }
        elif success_count > 0 and failed_count > 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Partial Success',
                    'message': f'Sent messages to {success_count} record(s), failed for {failed_count} record(s)',
                    'type': 'warning',
                }
            }
        else:
            raise UserError(f"Failed to send messages to any records. {failed_count} failures.") 