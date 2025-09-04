# wizards/busy_vehicle_confirmation_wizard.py
from odoo import models, fields, api
from odoo.exceptions import UserError


class BusyVehicleConfirmationWizard(models.TransientModel):
    _name = 'trucking_planning.vehicle.confirmation.wizard'
    _description = 'Busy Vehicle Assignment Confirmation Wizard'

    vehicle_driver_history_id = fields.Many2one(
        'trucking_planning.vehicle.driver.history',
        string='Vehicle-Driver Pair',
        required=True,
        readonly=True
    )

    current_trip_id = fields.Many2one(
        'trucking_planning.trip',
        string='Current Trip',
        readonly=True
    )

    new_trip_id = fields.Many2one(
        'trucking_planning.trip',
        string='New Trip',
        required=True,
        readonly=True
    )

    # Current trip details
    current_trip_plan_name = fields.Char(
        related='current_trip_id.plan_id.name',
        string='Plan',
        readonly=True
    )

    current_trip_client = fields.Char(
        related='current_trip_id.client_id.name',
        string='Client',
        readonly=True
    )
    current_trip_route = fields.Char(
        related='current_trip_id.route_id.name',
        string='Route',
        readonly=True
    )
    current_trip_etd = fields.Datetime(
        related='current_trip_id.plan_estimate_time_departure',
        string='Estimate Time Departure',
        readonly=True
    )

    current_trip_eta = fields.Datetime(
        related='current_trip_id.plan_estimate_time_arrival',
        string='Estimate Time Arrival',
        readonly=True
    )

    current_trip_status = fields.Selection(
        related='current_trip_id.status',
        string='Status',
        readonly=True
    )

    # New trip details
    new_trip_plan_name = fields.Char(
        related='new_trip_id.plan_id.name',
        string='Plan',
        readonly=True
    )

    new_trip_client = fields.Char(
        related='new_trip_id.client_id.name',
        string='Client',
        readonly=True
    )

    new_trip_etd = fields.Datetime(
        related='new_trip_id.plan_estimate_time_departure',
        string='Estimate Time Departure',
        readonly=True
    )

    new_trip_eta = fields.Datetime(
        related='new_trip_id.plan_estimate_time_arrival',
        string='Estimate Time Arrival',
        readonly=True
    )
    new_trip_route = fields.Char(
        related='new_trip_id.route_id.name',
        string='Route',
        readonly=True
    )

    vehicle_name = fields.Char(
        related='vehicle_driver_history_id.vehicle_id.name',
        string='Vehicle',
        readonly=True
    )

    driver_name = fields.Char(
        related='vehicle_driver_history_id.driver_id.name',
        string='Driver',
        readonly=True
    )

    warning_message = fields.Text(
        string='Warning',
        readonly=True,
        default='Warning: This truck-driver pair is already assigned to another trip during the overlapping time period!'
    )

    def action_confirm_assignment(self):
        if not self.new_trip_id:
            raise UserError("No new trip available for assignment.")

        # queued job processing unassign and reassign vehicle-driver pair
        self.with_delay().process_busy_vehicle_reassignment()
        return {'type': 'ir.actions.act_window_close'}

    def process_busy_vehicle_reassignment(self):
        conflicting_trip = self.vehicle_driver_history_id.get_conflicting_trip(self.new_trip_id)

        if conflicting_trip and conflicting_trip.exists():
            conflicting_trip.vehicle_driver_history_id = False
            conflicting_trip.message_post(
                body=f"Vehicle-driver pair '{self.vehicle_driver_history_id.name}' has been unassigned and reassigned to another trip.",
                message_type='notification'
            )

        # Assign to new trip
        if self.new_trip_id and self.new_trip_id.exists():
            self.new_trip_id.vehicle_driver_history_id = self.vehicle_driver_history_id
            self.new_trip_id.message_post(
                body=f"Vehicle-driver pair '{self.vehicle_driver_history_id.name}' has been assigned to this trip (reassigned from another trip).",
                message_type='notification'
            )

    def action_cancel(self):
        """Cancel the assignment"""
        return {'type': 'ir.actions.act_window_close'}