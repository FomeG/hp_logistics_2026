from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
import logging
from ...services.res_partner_service import ResPartnerService
from ...services.vehicle_service import VehicleService
from odoo.addons.hp_components.models import constants
from odoo.addons.hp_components.services.partner_service import PartnerService


_logger = logging.getLogger(__name__)

class ImportVehicleDriverWizard(models.TransientModel):
    _name = 'trucking_planning.import_vehicle_driver_wizard'
    _description = 'Import Vehicle and Driver Wizard'

    branch_id = fields.Many2one('trucking_planning.branch', string='Branch', required=True)
    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name', help='Select the Excel sheet to import')
    available_sheets = fields.Text(string='Available Sheets', readonly=True)

    def _normalize_text(self, text):
        """Normalize text using the same logic as UniqueNormalizedNameMixin"""
        if not text:
            return ''
        import unicodedata
        import re
        text = unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8')
        text = text.lower().strip()
        text = re.sub(r'\s+', '', text)  # Remove ALL spaces completely
        return text

    def _get_engine_type(self, machine_type):
        """Get engine type with fuzzy matching for Vietnamese machine types"""
        if not machine_type:
            return constants.VehicleEngineType.SMALL
        
        normalized = machine_type.lower().strip()
        
        # Big engine variations
        big_variations = [
            'máy to', 'may to', 'mayto', 'máy tô', 'may to', 
            'MÁY TO', 'MAY TO', 'May To', 'may to', 'may  to',
            'máy  to', 'may  to', 'mayto', 'may-to', 'may_to',
            'máy tô', 'may to', 'mayto', 'may to', 'may to',
            'máy tô', 'may to', 'mayto', 'may to', 'may to'
        ]
        
        # Small engine variations  
        small_variations = [
            'máy bé', 'may be', 'maybe', 'máy bê', 'may be',
            'MÁY BÉ', 'MAY BE', 'May Be', 'may be', 'may  be',
            'máy  bé', 'may  be', 'maybe', 'may-be', 'may_be',
            'máy bê', 'may be', 'maybe', 'may be', 'may be'
        ]
        
        # Check for big engine
        for variation in big_variations:
            if variation in normalized or normalized in variation:
                return constants.VehicleEngineType.SMALL

        
        # Check for small engine
        for variation in small_variations:
            if variation in normalized or normalized in variation:
                return constants.VehicleEngineType.SMALL
        
        # Default fallback with logging
        _logger.warning(f"Unknown machine type '{machine_type}', defaulting to 'small'")
        return constants.VehicleEngineType.SMALL

    @api.onchange('file', 'file_name')
    def _onchange_file(self):
        if self.file and self.file_name:
            self.sheet_name = ''
            file_content = base64.b64decode(self.file)
                
            # Check if file content is valid
            if len(file_content) == 0:
                raise Exception("File is empty")
            
                # check file type
            if not self.file_name.lower().endswith(('.xlsx', '.xls')):
                raise UserError(_("Only Excel files (.xlsx, .xls) are allowed."))

            engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
            xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
            self.available_sheets = ', '.join(xl.sheet_names)
            if len(xl.sheet_names) >= 1:
                self.sheet_name = xl.sheet_names[0]
        else:
            self.sheet_name = ''
            self.available_sheets = ''

    def get_available_sheets(self):
        file_content = base64.b64decode(self.file)
        engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
        xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
        return xl.sheet_names

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_('Please upload a file.'))

        vehicle_model = self.env['fleet.vehicle.hpl']
        driver_model = self.env['res.partner.driver']

        file_content = base64.b64decode(self.file)

        engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
        xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
        sheet_names = xl.sheet_names
        sheet_to_import = None

        sheet_to_import = sheet_names[0]
        if self.sheet_name and self.sheet_name in sheet_names:
            sheet_to_import = self.sheet_name

        # Read the Excel file starting from row 1 (header row)
        df = pd.read_excel(io.BytesIO(file_content),
                            engine=engine,
                            sheet_name=sheet_to_import,
                            header=0)  # Header is in row 1

        # Check for required columns based on the image data
        required_columns = ['Mã xe', 'Biển số', 'Họ tên lái xe', 'điện thoại', 'loại máy']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            available_cols = [str(col) for col in df.columns]
            raise UserError(_('Missing required columns: %s\n\nAvailable columns in sheet "%s":\n%s') %
                            (', '.join(missing_columns), sheet_to_import, '\n- '.join(available_cols)))

        imported_vehicles = 0
        updated_vehicles = 0
        imported_drivers = 0
        updated_drivers = 0
        skipped_rows = 0

        for index, row in df.iterrows():
            # Skip rows with empty license plate (required for vehicle)
            license_plate = str(row['Biển số']).strip() if pd.notna(row['Biển số']) else ''
            if not license_plate:
                skipped_rows += 1
                continue

            # Process Driver Data
            driver_name = str(row['Họ tên lái xe']).strip() if pd.notna(row['Họ tên lái xe']) else ''
            driver_phone = str(row['điện thoại']).strip() if pd.notna(row['điện thoại']) else ''
            
            driver_record = None
            if driver_name and driver_phone:
                partner_service = PartnerService(self.env)
                partner_main_type_driver = partner_service.get_partner_main_type_driver()
                # Check if driver exists by phone number (unique constraint)
                existing_driver = driver_model.search([('phone', '=', driver_phone), ('partner_main_type_id', '=', partner_main_type_driver.id)], limit=1)
                
                # Generate unique temporary values
                temp_suffix = driver_phone if driver_phone else f'TEMP_{index}'
                driver_vals = {
                    'partner_main_type_id': partner_main_type_driver.id,
                    'name': driver_name,
                    'phone': driver_phone,
                    'ref': f'DUMMY_CCCD_{temp_suffix}',  # Temporary value, needs manual update
                    'license_number': f'DUMMY_LICENSE_{temp_suffix}',  # Temporary value, needs manual update
                }
                
                if existing_driver:
                    existing_driver.write(driver_vals)
                    driver_record = existing_driver
                    updated_drivers += 1
                else:
                    driver_record = driver_model.create(driver_vals)
                    imported_drivers += 1

            # Process Vehicle Data
            trailer_number = str(row['số mooc']).strip() if pd.notna(row['số mooc']) else ''
            machine_type = str(row['loại máy']).strip() if pd.notna(row['loại máy']) else ''
            
            # Map machine type to engine type
            engine_type = self._get_engine_type(machine_type)
            
            # Process Trailer first (if exists) so we can assign it to the truck
            trailer_record = None
            if trailer_number:
                existing_trailer = vehicle_model.search([
                    ('license_plate', '=', trailer_number),
                    ('fake_category_type', '=', constants.VehicleModelCategory.TRAILER),
                ], limit=1)

                trailer_vals = {
                    'license_plate': trailer_number,
                    'fake_category_type': constants.VehicleModelCategory.TRAILER,
                    'fake_engine_type': constants.VehicleEngineType.SMALL,  # Trailer doesn't need engine type
                    'trucking_branch_id': self.branch_id.id,
                }
                
                if existing_trailer:
                    existing_trailer.write(trailer_vals)
                    trailer_record = existing_trailer
                else:
                    trailer_record = vehicle_model.create(trailer_vals)
            
            # Check if vehicle exists by normalized name (to handle unique constraint)
            existing_vehicle = vehicle_model.search([
                ('license_plate', '=', license_plate),
                ('fake_category_type', '=', constants.VehicleModelCategory.TRUCK),
            ], limit=1)
            
            vehicle_vals = {
                'license_plate': license_plate,
                'fake_category_type': constants.VehicleModelCategory.TRUCK,
                'fake_engine_type': engine_type,
                'trucking_branch_id': self.branch_id.id,
            }
            
            # Set primary driver if we have a driver record
            if driver_record:
                vehicle_vals['driver_id'] = driver_record.partner_id.id

            # Assign trailer to the truck (if we have a trailer record)
            if trailer_record:
                vehicle_vals['trailer_id'] = trailer_record.vehicle_id.id

            if existing_vehicle:
                existing_vehicle.write(vehicle_vals)
                updated_vehicles += 1
            else:
                vehicle_model.create(vehicle_vals)
                imported_vehicles += 1

        message_parts = [
            _('Import completed from sheet "%s"') % sheet_to_import,
            _('- New vehicles: %s') % imported_vehicles,
            _('- Updated vehicles: %s') % updated_vehicles,
            _('- New drivers: %s') % imported_drivers,
            _('- Updated drivers: %s') % updated_drivers,
        ]

        if skipped_rows > 0:
            message_parts.append(_('- Skipped rows (no license plate): %s') % skipped_rows)

        if imported_drivers > 0 or updated_drivers > 0:
            message_parts.append(_('\n⚠️ Note: Drivers imported with temporary CCCD and License Number values. Please update these manually.'))

        message = '\n'.join(message_parts)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import Success'),
                'message': message,
                'sticky': False,
            }
        } 