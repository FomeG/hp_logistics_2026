from odoo.addons.component.core import Component
from odoo import fields

class PlanLineListener(Component):
    _name = 'trucking_planning.plan_line_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.plan.line']

    def on_record_create(self, record, fields=None):
        self._create_trucks_for_plan_line(record)

    def on_record_write(self, record, fields=None):
        if 'number_of_trucks' in (fields or []):
            self._create_trucks_for_plan_line(record)

    def _create_trucks_for_plan_line(self, record):
        if not record.number_of_trucks or record.number_of_trucks <= 0:
            return

        existing_trucks_count = len(record.trip_ids)
        trucks_to_create = record.number_of_trucks - existing_trucks_count

        if trucks_to_create <= 0:
            return

        # Create the new trucks
        trucks_created = []
        for i in range(trucks_to_create):
            truck_vals = {
                'plan_line_id': record.id,
                'container_type': record.plan_id.container_type,
                'container_size': '40',
                'weight_class': 'mix',
            }

            trip = record.env['trucking_planning.trip'].create(truck_vals)
            trucks_created.append(trip.id)

        if trucks_created:
            message = f"Created {len(trucks_created)} truck(s) for {record.client_id.name}"
            record.message_post(body=message, message_type='notification')