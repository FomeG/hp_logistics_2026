from odoo import models, fields, api
from odoo.exceptions import UserError


class BusyVehicleConfirmationWizard(models.TransientModel):
    _name = 'trucking_planning.vehicle.confirmation.wizard'
    _description = 'Busy Vehicle Assignment Confirmation Wizard'

    vehicle_assignment_log_id = fields.Many2one(
        'fleet.vehicle.assignation.log',
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
        string='Plan ',
        readonly=True
    )

    new_trip_client = fields.Char(
        related='new_trip_id.client_id.name',
        string='Client ',
        readonly=True
    )

    new_trip_etd = fields.Datetime(
        related='new_trip_id.plan_estimate_time_departure',
        string='Estimate Time Departure ',
        readonly=True
    )

    new_trip_eta = fields.Datetime(
        related='new_trip_id.plan_estimate_time_arrival',
        string='Estimate Time Arrival ',
        readonly=True
    )
    new_trip_route = fields.Char(
        related='new_trip_id.route_id.name',
        string='Route ',
        readonly=True
    )

    vehicle_name = fields.Char(
        related='vehicle_assignment_log_id.vehicle_id.name',
        string='Vehicle',
        readonly=True
    )

    driver_name = fields.Char(
        related='vehicle_assignment_log_id.driver_id.name',
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

        self.new_trip_id.vehicle_assignment_log_id = self.vehicle_assignment_log_id
        self.new_trip_id.message_post(
            body="Vehicle-driver pair '%s - %s' has been reassigned to this trip from another trip." % (
                self.vehicle_assignment_log_id.vehicle_id.name,
                self.vehicle_assignment_log_id.driver_id.name
            ),
            message_type='notification'
        )

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel(self):
        """Cancel the assignment"""
        return {'type': 'ir.actions.act_window_close'}