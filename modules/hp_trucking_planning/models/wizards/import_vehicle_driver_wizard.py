from odoo import models, fields, api, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
import logging
from odoo.addons.hp_components.services.department_service import DepartmentService

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
            return 'small'
        
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
                return 'big'
        
        # Check for small engine
        for variation in small_variations:
            if variation in normalized or normalized in variation:
                return 'small'
        
        # Default fallback with logging
        _logger.warning(f"Unknown machine type '{machine_type}', defaulting to 'small'")
        return 'small'

    @api.onchange('file', 'file_name')
    def _onchange_file(self):
        if self.file and self.file_name:
            self.sheet_name = ''
            try:
                file_content = base64.b64decode(self.file)
                
                # Check if file content is valid
                if len(file_content) == 0:
                    raise Exception("File is empty")
                
                # Try to determine the correct engine based on file extension
                if self.file_name.endswith('.xls'):
                    # For .xls files, try openpyxl first (works with newer pandas), then xlrd
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                        engine = 'openpyxl'
                    except Exception as e1:
                        try:
                            xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                            engine = 'xlrd'
                        except Exception as e2:
                            # Check if it's a version issue and provide specific guidance
                            if "version" in str(e1).lower() or "version" in str(e2).lower():
                                raise Exception("Excel library version issue detected. Please upgrade: pip install --upgrade xlrd openpyxl")
                            else:
                                raise Exception(f"Both engines failed for .xls file. openpyxl: {str(e1)}, xlrd: {str(e2)}")
                elif self.file_name.endswith('.xlsx'):
                    engine = 'openpyxl'
                else:
                    # Try both engines for unknown extensions
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                        engine = 'openpyxl'
                    except Exception as e1:
                        try:
                            xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                            engine = 'xlrd'
                        except Exception as e2:
                            # Check if it's a version issue and provide specific guidance
                            if "version" in str(e1).lower() or "version" in str(e2).lower():
                                raise Exception("Excel library version issue detected. Please upgrade: pip install --upgrade xlrd openpyxl")
                            else:
                                raise Exception(f"Both engines failed. openpyxl: {str(e1)}, xlrd: {str(e2)}")
                
                xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
                self.available_sheets = ', '.join(xl.sheet_names)
                if len(xl.sheet_names) >= 1:
                    self.sheet_name = xl.sheet_names[0]
            except Exception as e:
                error_msg = str(e)
                if "version" in error_msg.lower():
                    error_msg = "Excel library version issue detected. Please upgrade: pip install --upgrade xlrd openpyxl"
                else:
                    error_msg = f'Cannot read Excel file: {error_msg}'
                _logger.error(error_msg)
                self.available_sheets = error_msg
        else:
            self.sheet_name = ''
            self.available_sheets = ''

    def get_available_sheets(self):
        if not self.file or not self.file_name:
            return []
        try:
            file_content = base64.b64decode(self.file)
            
            # Check if file content is valid
            if len(file_content) == 0:
                raise Exception("File is empty")
            
            # Try to determine the correct engine based on file extension
            if self.file_name.endswith('.xls'):
                # For .xls files, try openpyxl first (works with newer pandas), then xlrd
                try:
                    xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                    engine = 'openpyxl'
                    _logger.info("Using openpyxl for .xls file")
                except Exception as e1:
                    _logger.info(f"openpyxl failed for .xls: {str(e1)}")
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                        engine = 'xlrd'
                        _logger.info("Using xlrd for .xls file")
                    except Exception as e2:
                        _logger.info(f"xlrd failed for .xls: {str(e2)}")
                        raise Exception(f"Both engines failed for .xls file. openpyxl: {str(e1)}, xlrd: {str(e2)}")
            elif self.file_name.endswith('.xlsx'):
                engine = 'openpyxl'
            else:
                # Try both engines for unknown extensions
                try:
                    xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                    engine = 'openpyxl'
                except Exception as e1:
                    _logger.info(f"openpyxl failed: {str(e1)}")
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                        engine = 'xlrd'
                    except Exception as e2:
                        _logger.info(f"xlrd failed: {str(e2)}")
                        raise Exception(f"Both engines failed. openpyxl: {str(e1)}, xlrd: {str(e2)}")
            
            xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
            _logger.info(f"Successfully read Excel file with engine: {engine}, Sheets: {xl.sheet_names}")
            return xl.sheet_names
        except Exception as e:
            return []

    def action_import(self):
        self.ensure_one()
        if not self.file:
            raise UserError(_('Please upload a file.'))
        
        try:
            file_content = base64.b64decode(self.file)
            
            # Try to determine the correct engine based on file extension
            if self.file_name.endswith('.xls'):
                # For .xls files, try openpyxl first (works with newer pandas), then xlrd
                try:
                    xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                    engine = 'openpyxl'
                    _logger.info("Using openpyxl for .xls file")
                except Exception as e1:
                    _logger.info(f"openpyxl failed for .xls: {str(e1)}")
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                        engine = 'xlrd'
                        _logger.info("Using xlrd for .xls file")
                    except Exception as e2:
                        _logger.info(f"xlrd failed for .xls: {str(e2)}")
                        raise Exception(f"Both engines failed for .xls file. openpyxl: {str(e1)}, xlrd: {str(e2)}")
            elif self.file_name.endswith('.xlsx'):
                engine = 'openpyxl'
            else:
                # Try both engines for unknown extensions
                try:
                    xl = pd.ExcelFile(io.BytesIO(file_content), engine='openpyxl')
                    engine = 'openpyxl'
                except Exception as e1:
                    _logger.info(f"openpyxl failed: {str(e1)}")
                    try:
                        xl = pd.ExcelFile(io.BytesIO(file_content), engine='xlrd')
                        engine = 'xlrd'
                    except Exception as e2:
                        _logger.info(f"xlrd failed: {str(e2)}")
                        raise Exception(f"Both engines failed. openpyxl: {str(e1)}, xlrd: {str(e2)}")
            
            xl = pd.ExcelFile(io.BytesIO(file_content), engine=engine)
            sheet_names = xl.sheet_names
            sheet_to_import = None

            if self.sheet_name:
                if self.sheet_name in sheet_names:
                    sheet_to_import = self.sheet_name
                else:
                    raise UserError(_('Sheet "%s" not found in file.\nAvailable sheets: %s') % (
                    self.sheet_name, ', '.join(sheet_names)))
            else:
                if len(sheet_names) == 1:
                    sheet_to_import = sheet_names[0]
                else:
                    raise UserError(
                        _('Multiple sheets found. Please specify sheet name.\nAvailable sheets: %s') % ', '.join(
                            sheet_names))

            # Read the Excel file starting from row 1 (header row)
            df = pd.read_excel(io.BytesIO(file_content),
                               engine=engine,
                               sheet_name=sheet_to_import,
                               header=0)  # Header is in row 1

        except Exception as e:
            error_msg = str(e)
            if "version" in error_msg.lower():
                error_msg = "Excel library version issue detected. Please upgrade: pip install --upgrade xlrd openpyxl"
            else:
                error_msg = f'Error reading file: {error_msg}'
            raise UserError(_(error_msg))

        # Check for required columns based on the image data
        required_columns = ['Mã xe', 'Biển số', 'Họ tên lái xe', 'điện thoại', 'loại máy']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            available_cols = [str(col) for col in df.columns]
            raise UserError(_('Missing required columns: %s\n\nAvailable columns in sheet "%s":\n%s') %
                            (', '.join(missing_columns), sheet_to_import, '\n- '.join(available_cols)))

        vehicle_model = self.env['trucking_planning.vehicle']
        driver_model = self.env['trucking_planning.driver']
        
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
                # Check if driver exists by phone number (unique constraint)
                existing_driver = driver_model.search([('phone_number', '=', driver_phone)], limit=1)
                
                # Generate unique temporary values
                temp_suffix = driver_phone if driver_phone else f'TEMP_{index}'
                driver_vals = {
                    'name': driver_name,
                    'phone_number': driver_phone,
                    'cccd': f'DUMMY_CCCD_{temp_suffix}',  # Temporary value, needs manual update
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
            vehicle_code = str(row['Mã xe']).strip() if pd.notna(row['Mã xe']) else ''
            trailer_number = str(row['số mooc']).strip() if pd.notna(row['số mooc']) else ''
            machine_type = str(row['loại máy']).strip() if pd.notna(row['loại máy']) else ''
            
            # Map machine type to engine type
            engine_type = self._get_engine_type(machine_type)
            
            # Process Trailer first (if exists) so we can assign it to the truck
            trailer_record = None
            if trailer_number:
                # Check if trailer exists by normalized name (to handle unique constraint)
                normalized_trailer_name = self._normalize_text(trailer_number)
                existing_trailer = vehicle_model.search([('normalized_name', '=', normalized_trailer_name)], limit=1)
                _logger.info(f"Trailer search: '{trailer_number}' -> normalized: '{normalized_trailer_name}' -> found: {bool(existing_trailer)}")
                
                trailer_vals = {
                    'name': trailer_number,
                    'normalized_name': normalized_trailer_name,  # Explicitly set normalized_name
                    'type': 'trailer',
                    'branch_id': self.branch_id.id,
                    'active': True,
                }
                
                if existing_trailer:
                    existing_trailer.write(trailer_vals)
                    trailer_record = existing_trailer
                else:
                    trailer_record = vehicle_model.create(trailer_vals)
            
            # Check if vehicle exists by normalized name (to handle unique constraint)
            normalized_license_plate = self._normalize_text(license_plate)
            existing_vehicle = vehicle_model.search([('normalized_name', '=', normalized_license_plate)], limit=1)
            _logger.info(f"Vehicle search: '{license_plate}' -> normalized: '{normalized_license_plate}' -> found: {bool(existing_vehicle)}")
            
            vehicle_vals = {
                'name': license_plate,
                'normalized_name': normalized_license_plate,  # Explicitly set normalized_name
                'type': 'truck',
                'engine_type': engine_type,
                'branch_id': self.branch_id.id,
                'active': True,
            }
            
            # Set primary driver if we have a driver record
            if driver_record:
                vehicle_vals['primary_driver_id'] = driver_record.id
            
            # Assign trailer to the truck (if we have a trailer record)
            if trailer_record:
                vehicle_vals['trailer_id'] = trailer_record.id
            
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