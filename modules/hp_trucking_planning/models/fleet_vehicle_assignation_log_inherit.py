from odoo import models, fields, api
from ..services.res_partner_service import ResPartnerService
from odoo.addons.hp_components.models import constants

class FleetVehicleAssignationLogInherit(models.Model):
    _inherit = 'fleet.vehicle.assignation.log'

    # driver_id = fields.Many2one(
    #     domain=[('type', '=', ResPartnerService.PARTNER_TYPE_DRIVER)]
    # )
    is_busy = fields.Boolean(
        string="Busy",
        compute="_compute_is_busy",
        search="_search_is_busy"
    )

    def _current_trip(self):
        Trip = self.env["trucking_planning.trip"]
        trip_id = self.env.context.get("trip_id")
        trip = Trip.browse(trip_id) if trip_id else Trip.browse()
        return trip if trip and trip.id else None

    def _get_trip_model(self):
        return self.env["trucking_planning.trip"]

    def _busy_pair_ids_for_trip(self, trip):
        if not trip or not trip.plan_estimate_time_departure or not trip.plan_estimate_time_arrival:
            return set()

        Trip = self._get_trip_model()
        busy_ids = set()
        domain = [
            ("id", "!=", trip.id),
            ("vehicle_assignment_log_id", "!=", False),
            ("plan_estimate_time_departure", "<=", trip.plan_estimate_time_arrival),
            ("plan_estimate_time_arrival", ">=", trip.plan_estimate_time_departure),
            ("vehicle_assignment_log_id.date_end", "=", False),
        ]

        groups = Trip.read_group(
            domain,
            fields=["vehicle_assignment_log_id"],
            groupby=["vehicle_assignment_log_id"],
            lazy=False,
        )
        for g in groups:
            if g.get("vehicle_assignment_log_id"):
                busy_ids.add(g["vehicle_assignment_log_id"][0])

        current_running_trips = Trip.search([
            ('vehicle_assignment_log_id', '!=', False),
            ('is_current', '=', True),
            ('status', '=', constants.TripStatus.ON_ROUTE),
        ])
        for t in current_running_trips:
            if t.vehicle_assignment_log_id:
                busy_ids.add(t.vehicle_assignment_log_id.id)

        return busy_ids

    def _compute_is_busy(self):
        trip = self._current_trip()
        busy_ids = self._busy_pair_ids_for_trip(trip)
        for rec in self:
            rec.is_busy = rec.id in busy_ids

    def _search_is_busy(self, operator, value):
        if operator not in ("=", "=="):
            return []
        trip = self._current_trip()
        busy_ids = self._busy_pair_ids_for_trip(trip)
        base = [("date_end", "=", False)]
        if bool(value):
            return base + [("id", "in", list(busy_ids) or [0])]
        else:
            return base + [("id", "not in", list(busy_ids) or [0])]

    def action_assign_to_trip(self):
        """Assign this pair to the trip passed via context."""
        trip = self._current_trip()
        conflicting_trip = trip.get_conflicting_trip(self)
        if conflicting_trip:
            warning = "The selected truck-driver pair is already assigned to another trip. Do you want to proceed?\n\n"
            return {
                'name': 'Confirm assigning a busy truck-driver pair.',
                'type': 'ir.actions.act_window',
                'res_model': 'trucking_planning.vehicle.confirmation.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_vehicle_assignment_log_id': self.id,
                    'default_current_trip_id': conflicting_trip.id,
                    'default_new_trip_id': trip.id,
                    'default_warning_message': warning,
                }
            }
        else:
            trip.vehicle_assignment_log_id = self.id
            return {"type": "ir.actions.act_window_close"}