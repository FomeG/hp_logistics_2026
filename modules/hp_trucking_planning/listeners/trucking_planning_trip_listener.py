from odoo.addons.component.core import Component
from odoo import fields

class TripListener(Component):
    _name = 'trucking_planning.trip_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.trip']

    def on_record_create(self, record, fields=None):
        """Tự động set plan_id từ plan_line_id khi tạo trip mới"""
        if record.plan_line_id and not record.plan_id:
            record.plan_id = record.plan_line_id.plan_id

    def on_record_write(self, record, fields=None):
        if 'vehicle_driver_history_id' in fields and record.vehicle_driver_history_id:
            self.with_delay().process_vehicle_driver_reassignment(record)


    def process_vehicle_driver_reassignment(self, record):
        conflicting_trips = record.vehicle_driver_history_id.get_conflicting_trip(record)

        if conflicting_trips and conflicting_trips.exists():
            for conflicting_trip in conflicting_trips:
                conflicting_trip.vehicle_driver_history_id = False
                conflicting_trip.message_post(
                    body=f"Vehicle-driver pair '{record.vehicle_driver_history_id.name}' has been unassigned and reassigned to another trip.",
                    message_type='notification'
                )
