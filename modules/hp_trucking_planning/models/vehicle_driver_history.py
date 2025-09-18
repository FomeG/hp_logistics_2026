from odoo import models, fields, api
from ..services.res_partner_service import ResPartnerService
import logging

_logger = logging.getLogger(__name__)

class VehicleDriverHistory(models.Model):

    _name = "trucking_planning.vehicle.driver.history"
    _description = "History of vehicle driver history"
    _order = "create_date desc"

    name = fields.Char(
        string='Name',
        compute='_compute_vehicle_driver_history_name',
        index=True,
        store=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        index=True,
    )
    driver_id = fields.Many2one(
        comodel_name='res.partner',
        index=True,
        domain=[('type','=', ResPartnerService.PARTNER_TYPE_DRIVER)]
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    end_date = fields.Date(
        string='End date',
        index=True
    )
    _sql_constraints = [
        ('vehicle_open_unique', 'UNIQUE(vehicle_id) WHERE (end_date IS NULL OR end_date = False)', 'A vehicle can only have one open driver assignment at a time.')
    ]

    @api.depends('vehicle_id', 'driver_id')
    def _compute_vehicle_driver_history_name(self):
        for record in self:
            record.name = f"{record.driver_id.name} - {record.vehicle_id.name}"

    # temp field to check if pair is busy on the current trip period
    # this field is only used for UI
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
        domain = [
            ("id", "!=", trip.id),
            ("vehicle_driver_history_id", "!=", False),
            ("plan_estimate_time_departure", "<=", trip.plan_estimate_time_arrival),
            ("plan_estimate_time_arrival", ">=", trip.plan_estimate_time_departure),
            ("vehicle_driver_history_id.end_date", "=", False),
        ]

        groups = Trip.read_group(
            domain,
            fields=["vehicle_driver_history_id"],
            groupby=["vehicle_driver_history_id"],
            lazy=False,
        )
        busy_ids = []
        for g in groups:
            vh = g.get("vehicle_driver_history_id")
            if vh and isinstance(vh, (list, tuple)):
                busy_ids.append(vh[0])
        return set(busy_ids)

    def _compute_is_busy(self):
        trip = self._current_trip()
        busy_ids = self._busy_pair_ids_for_trip(trip)
        for rec in self:
            rec.is_busy = rec.id in busy_ids

    # used for search
    def _search_is_busy(self, operator, value):
        if operator not in ("=", "=="):
            return []
        trip = self._current_trip()
        busy_ids = self._busy_pair_ids_for_trip(trip)
        base = [("end_date", "=", False)]
        if bool(value):
            return base + [("id", "in", list(busy_ids) or [0])]
        else:
            return base + [("id", "not in", list(busy_ids) or [0])]

    def action_assign_to_trip(self):
        """Assign this pair to the trip passed via context."""
        trip = self._current_trip()
        conflicting_trip = trip.get_conflicting_trip(self)  # Updated to call from Trip model

        # Check if this pair is busy (has overlapping time with other trips)
        if conflicting_trip:
            # Find the current trip that's causing the conflict
            return {
                'name': 'Confirm assigning a busy truck-driver pair.',
                'type': 'ir.actions.act_window',
                'res_model': 'trucking_planning.vehicle.confirmation.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_vehicle_driver_history_id': self.id,
                    'default_current_trip_id': conflicting_trip.id,
                    'default_new_trip_id': trip.id,
                }
            }
        else:
            trip.vehicle_driver_history_id = self.id
            return {
                "type": "ir.actions.act_window_close"  # close popup
            }