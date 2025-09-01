from odoo.addons.component.core import Component

class TruckingPlanningVehicleListener(Component):
    _name = 'trucking_planning.vehicle.listener'
    _description = 'Trucking Planning Vehicle Listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.vehicle']

    def on_record_create(self, record, fields=None):
        record.with_delay().assign_driver()

    def on_record_write(self, record, fields=None):
        record.with_delay().assign_driver()