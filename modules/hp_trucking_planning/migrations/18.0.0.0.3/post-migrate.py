from odoo import api, SUPERUSER_ID

def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})

    migrate_driver(env)
    migrate_client(env)
    migrate_shipping_line(env)
    migrate_vehicle(env)


def migrate_driver(env):
    data_drivers = []
    drivers = env['trucking_planning.driver'].search([])
    for driver in drivers:
        data_drivers.append({
            'type': 'driver',
            'name': driver.name,
            'phone': driver.phone_number,
            'cccd': driver.cccd,
            'license_number': driver.license_number,
            'contract_date': driver.contract_date,
        })
    
    if data_drivers:
        env['res.partner'].create(data_drivers)
    print(f"✅ Migrated drivers success")

def migrate_client(env):
    data_clients = []
    clients = env['trucking_planning.client'].search([])
    for client in clients:
        if not client.tax_number:
            continue

        vals = {
            'type': 'client',
            'code': client.code,
            'name': client.name,
            'street': client.address,
            'vat': client.tax_number,
            'branch_id': client.branch_id.id,
            'assign_user_id': client.assign_user_id.id,
            'phone': client.phone,
        }

        partner = env['res.partner'].search([('vat', '=', client.tax_number)], limit=1)
        if partner:
            partner.write(vals)
        else:
            data_clients.append(vals)

    if data_clients:
        env['res.partner'].create(data_clients)
    print(f"✅ Migrated client success")

def migrate_shipping_line(env):
    data_shipping_lines = []
    shipping_lines = env['trucking_planning.shipping_line'].search([])

    partner_main_type = env['partner.main.type'].search([('code', '=', 'shipping_line')], limit=1)
    if not partner_main_type:
        return False
    
    for shipping_line in shipping_lines:
        data_shipping_lines.append({
            'name': shipping_line.name,
            'partner_main_type_id': partner_main_type.id,
        })
    
    if data_shipping_lines:
        env['res.partner'].create(data_shipping_lines)
    print(f"✅ Migrated shipping line success")

def migrate_vehicle(env):
    vehicle_model = env['fleet.vehicle.model']
    vehicle_model_truck = vehicle_model.search([('vehicle_type', '=', 'truck')], limit=1)
    vehicle_model_trailer = vehicle_model.search([('vehicle_type', '=', 'trailer')], limit=1)

    if not vehicle_model_trailer or not vehicle_model_truck:
        return False

    # trailer
    data_trailers = []
    trailers = env['trucking_planning.vehicle'].search([('type', '=', 'trailer')])
    for trailer in trailers:
        data_trailers.append({
            'license_plate': trailer.name,
            'model_id': vehicle_model_trailer.id,
            'trucking_branch_id': trailer.branch_id.id,
            'acquisition_date': trailer.registration_date,
            'is_rented': trailer.is_rented,
        })
    
    if data_trailers:
        env['fleet.vehicle'].create(data_trailers)

    # truck
    data_trucks = []
    trucks = env['trucking_planning.vehicle'].search([('type', '=', 'truck')])
    for truck in trucks:
        trailer_id = False
        if truck.trailer_id:
            fleet_trailer = env['fleet.vehicle'].search([
                ('type', '=', 'trailer'),
                ('license_plate', '=', truck.trailer_id.name),
                ('trucking_branch_id', '=', truck.brbranch_id.id),
            ], limit=1)
            trailer_id = fleet_trailer.id if fleet_trailer else False
        
        driver_id = False
        if truck.primary_driver_id:
            partner = env['res.partner'].search([
                ('type', '=', 'driver'),
                ('phone', '=', truck.primary_driver_id.phone),
            ], limit=1)
            driver_id = partner.id if partner else False
        
        data_trucks.append({
            'license_plate': truck.name,
            'model_id': vehicle_model_truck.id,
            'trucking_branch_id': truck.branch_id.id,
            'acquisition_date': truck.registration_date,
            'is_rented': truck.is_rented,
            'engine_type': truck.engine_type,
            'trailer_id': trailer_id,
            'driver_id': driver_id,
            'fuel_rate_inferior_20': truck.fuel_rate_inferior_20,
            'fuel_rate_superior_20': truck.fuel_rate_superior_20,
            'fuel_rate_mix': truck.fuel_rate_mix,
        })

    if data_trucks:
        env['fleet.vehicle'].create(data_trucks)
    print(f"✅ Migrated vehicle success")