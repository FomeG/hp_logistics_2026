from odoo import models, fields, _
from odoo.exceptions import UserError
import pandas as pd
import io
import base64
import re

class ImportRouteWizard(models.TransientModel):
    _name = 'trucking_planning.import_route_wizard'
    _description = 'Import Route Wizard'

    to_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string='To State',
        domain="[('country_id.code', '=', 'VN')]",
        required=True
    )
    file = fields.Binary(string='Upload File (Excel)', required=True)
    file_name = fields.Char(string='File Name')
    sheet_name = fields.Char(string='Sheet Name', help='Select the Excel sheet to import')


    def _validate_file(self, file_content):
        result = {
            'status': False,
            'message': '',
            'data': []
        }

        # check file type
        if not self.file_name.lower().endswith(('.xlsx', '.xls')):
            result['message'] = _("Only Excel files (.xlsx, .xls) are allowed.")
            return result
        
        engine = 'xlrd' if self.file_name.endswith('.xls') else 'openpyxl'
        convert_file_content = io.BytesIO(file_content)
        xl = pd.ExcelFile(convert_file_content, engine)
        available_sheets = xl.sheet_names

        # check sheet name to use import
        sheet_import = self.sheet_name or available_sheets[0]
        if sheet_import not in available_sheets:
            result['message'] = _('Sheet "%s" not found in file.') % self.sheet_name
            return result
        
        # check header in row 3
        df = pd.read_excel(
            io.BytesIO(file_content),
            engine=engine,
            sheet_name=sheet_import,
            header=2
        )

        required_columns = ['STT', 'Tiền đường', 'Lương chuyến', 'Tiền Vé', 'Số Km']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['message'] = _('Missing required columns: %s') % ", ".join(missing_columns)
            return result
        
        # check header
        location_header = df.columns[1]
        pattern = r"^từ/đến\s*-\s*(.+)$"
        match = re.match(pattern, str(location_header).strip(), re.IGNORECASE)
        if not match:
            result['message'] = _("Invalid header format. Expected 'Từ/đến - <location>', got: %s") % location_header
            return result

        # models
        model_location = self.env['location.base']
        model_state = self.env['res.country.state']

        # check to location
        location_name = re.sub(r'\s+', ' ', match.group(1).strip())
        to_location = model_location.search([
            ('type', '=', 'route_point'),
            ('name', 'ilike', location_name)
        ], limit=1)

        if not to_location:
            to_location = model_location.create({
                'name': location_name,
                'type': 'route_point',
                'state_id': self.to_state_id.id,
                'address': f"{location_name}, {self.to_state_id.name}",
            })

        #  build data
        current_state = False
        data = []
        for index, row in df.iterrows():
            address = row[location_header]
            if pd.isna(address):
                continue

            address = re.sub(r'\s+', ' ', address.strip())
            road_fee = row['Tiền đường']
            trip_salary = row['Lương chuyến']
            ticket_fee = row['Tiền Vé']
            distance_km = row['Số Km']
            
            is_row_state = pd.notna(address) and pd.isna(road_fee) and pd.isna(trip_salary) and pd.isna(ticket_fee) and pd.isna(distance_km)
            if is_row_state:
                state = model_state.search([
                    ('country_id.code', '=', 'VN'),
                    ('name', 'ilike', address)
                ], limit=1)

                if not state:
                    result['message'] = _("Invalid state: %s.") % address
                    return result

                current_state = state
                continue
                
            if current_state and not is_row_state:
                # build data
                data.append({
                    'from_location': {
                        'name': address,
                        'type': 'route_point',
                        'state_id': state.id,
                        'address': address,
                    },
                    'to_location': {
                        'id': to_location.id,
                    },
                    'route': {
                        'road_fee': float(road_fee) if pd.notna(road_fee) else 0,
                        'trip_salary': float(trip_salary) if pd.notna(trip_salary) else 0,
                        'ticket_fee': float(ticket_fee) if pd.notna(ticket_fee) else 0,
                        'distance_km': float(distance_km) if pd.notna(distance_km) else 0,
                    }
                })
            elif not current_state:
                result['message'] = _("Data row at line %s is missing a valid state %d.") % (index + 4)
                return result
        
        # remove data with duplicate name
        unique_data = {}
        for obj in data:
            name = obj['from_location']['name']
            unique_data[name] = obj

        return {
            'status': True,
            'message': '',
            'data': list(unique_data.values())
        }
    
    def _create_locations(self, data_array):
        Location = self.env['location.base']

        from_names_lower = list({
            data['from_location']['name'].lower()
            for data in data_array
            if data.get('from_location') and data['from_location'].get('name')
        })
        all_locations = Location.search([])
        exist_locations = all_locations.filtered(
            lambda loc: loc.name.strip().lower() in from_names_lower
        )
        location_map = {loc.name.lower(): loc for loc in exist_locations if loc.name}

        new_location_vals = []
        new_location_names = []
        for data in data_array:
            f = data.get('from_location', {})
            name_lower = f.get('name').lower()
            if name_lower not in location_map:
                new_location_vals.append({
                    'name': f.get('name'),
                    'type': f.get('type'),
                    'state_id': f.get('state_id'),
                    'address': f.get('address'),
                })
                new_location_names.append(name_lower)

        created_locations = Location.create(new_location_vals) if new_location_vals else Location
        for index, location in enumerate(created_locations):
            location_map[new_location_names[index]] = location

        return location_map

    def _create_routes(self, data_array, location_map):
        Route = self.env['route.base']

        route_vals_list = []
        for data in data_array:
            data_from_location = data.get('from_location', {})
            to_location_id = data.get('to_location', {}).get('id')
            from_location = location_map.get(data_from_location.get('name').lower())

            route_vals = data.get('route', {}).copy()
            route_vals.update({
                'from_location_id': from_location.id if from_location else False,
                'to_location_id': to_location_id,
            })
            route_vals_list.append(route_vals)


        pairs = {(route['from_location_id'], route['to_location_id']) for route in route_vals_list}
        exist_pairs = {
            (r.from_location_id.id, r.to_location_id.id)
            for r in Route.search([('from_location_id', 'in', [p[0] for p in pairs]),
                                ('to_location_id', 'in', [p[1] for p in pairs])])
        }

        new_vals = [route_valid for route_valid in route_vals_list if (route_valid['from_location_id'], route_valid['to_location_id']) not in exist_pairs]
        return Route.create(new_vals) if new_vals else Route

    def action_import(self):
        self.ensure_one()
        try:
            if not self.file:
                raise UserError(_('Please upload a file.'))
        
            file_content = base64.b64decode(self.file)

            validate = self._validate_file(file_content)
            if not validate['status']:
                raise UserError(validate['message'])
            
            data = validate['data']
            new_locations = self._create_locations(data)
            new_routes = self._create_routes(data, new_locations)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Success'),
                    'message': _("Import success: %s routes") % len(new_routes),
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(str(e))
