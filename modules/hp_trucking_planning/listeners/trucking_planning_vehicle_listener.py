from odoo.addons.component.core import Component

class TruckingPlanningVehicleListener(Component):
    _name = 'fleet.vehicle.listener'
    _description = 'Trucking Planning Vehicle Listener'
    _inherit = 'base.event.listener'
    _apply_on = ['fleet.vehicle']

    def on_record_create(self, record, fields=None):
        hpl_record = self.env['fleet.vehicle.hpl'].search([('vehicle_id', '=', record.id)], limit=1)
        if hpl_record:
            if not hpl_record.is_trailer and record.driver_id:
                hpl_record.with_delay().assign_driver()

    def on_record_write(self, record, fields=None):
        if 'driver_id' in fields:
            hpl_record = self.env['fleet.vehicle.hpl'].search([('vehicle_id', '=', record.id)], limit=1)
            if hpl_record and not hpl_record.is_trailer:
                hpl_record.with_delay().assign_driver()