from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta

class TruckingDashboard(models.Model):
    _name = 'trucking.dashboard'
    _description = 'Trucking Dashboard'

    name = fields.Char(
        default="Dashboard",
        readonly=True)

    filter_month = fields.Selection(
        selection='_get_month_selection',
        string="Month",
        default=lambda self: str(fields.Date.today().month),
    )
    filter_year = fields.Selection(
        selection='_get_year_selection',
        string="Year",
        default=lambda self: str(fields.Date.today().year),
    )

    selected_period = fields.Char(
        string="Selected Period",
        compute='_compute_selected_period',
        store=False,
    )
    total_trip_month = fields.Integer(
        string="Total Trip month",
        compute="_compute_totals_trip_month")

    total_trip_done = fields.Integer(
        string="Trip done",
        compute="_compute_totals_trip_month"
    )

    total_trip_cancelled = fields.Integer(
        string="Trip cancelled",
        compute="_compute_totals_trip_month"
    )

    top_truck_driver = fields.Text(
        string="Top truck - driver (by trips)",
        compute="_compute_top_truck_driver")

    all_drivers_stats = fields.Text(
        string="All Drivers Statistics",
        compute="_compute_all_drivers_stats"
    )

    total_trip_on_route = fields.Integer(
        string="Trip On Route",
        compute="_compute_totals_trip_month"
    )

    total_trip_stopped = fields.Integer(
        string="Trip Stopped",
        compute="_compute_totals_trip_month"
    )

    @api.depends('filter_month', 'filter_year')
    def _compute_totals_trip_month(self):
        Trip = self.env['trucking_planning.trip']

        for rec in self:
            start_date, end_date = rec._get_date_range()

            base_domain = [
                ('plan_date', '>=', start_date),
                ('plan_date', '<', end_date),
            ]

            # Total trips (excluding cancelled)
            rec.total_trip_month = Trip.search_count(
                base_domain + [('status', '!=', 'cancelled')]
            )

            # Done trips
            rec.total_trip_done = Trip.search_count(
                base_domain + [('status', '=', 'done')]
            )

            # Cancelled trips
            rec.total_trip_cancelled = Trip.search_count(
                base_domain + [('status', '=', 'cancelled')]
            )

            # On Route trips
            rec.total_trip_on_route = Trip.search_count(
                base_domain + [('status', '=', 'on_route')]
            )

            # Stopped trips
            rec.total_trip_stopped = Trip.search_count(
                base_domain + [('status', '=', 'stopped')]
            )

    @api.model
    def _get_month_selection(self):
        return [(str(i), f'Tháng {i}') for i in range(1, 13)]

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(year), str(year)) for year in range(current_year - 2, current_year + 2)]

    @api.depends('filter_month', 'filter_year')
    def _compute_selected_period(self):
        for rec in self:
            if rec.filter_month and rec.filter_year:
                month_name = dict(rec._get_month_selection()).get(rec.filter_month, '')
                rec.selected_period = f"{month_name} {rec.filter_year}"
            else:
                rec.selected_period = "Non-selected"

    def _get_date_range(self):
        self.ensure_one()

        if self.filter_month and self.filter_year:
            month = int(self.filter_month)
            year = int(self.filter_year)
        else:
            today = fields.Date.today()
            month = today.month
            year = today.year

        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        return start_date, end_date

    @api.depends('filter_month', 'filter_year')
    def _compute_top_truck_driver(self):
        """Top 5 xe - tài xế theo số chuyến"""
        for rec in self:
            start_date, end_date = rec._get_date_range()
            self.env.cr.execute("""
                    SELECT f.name AS truck, rp.name AS driver, COUNT(t.id) AS total
                    FROM trucking_planning_trip t
                    LEFT JOIN fleet_vehicle f ON f.id = t.truck_id
                    LEFT JOIN res_partner_driver rpd ON rpd.id = t.driver_id
                    LEFT JOIN res_partner rp ON rp.id = rpd.partner_id
                    WHERE t.status != 'cancelled'
                        AND t.plan_date >= %s
                        AND t.plan_date < %s
                    GROUP BY f.name, rp.name
                    ORDER BY total DESC
                    LIMIT 5
                """, (start_date, end_date))
            rows = self.env.cr.dictfetchall()
            if not rows:
                rec.top_truck_driver = "No data available."
            else:
                lines = [f"{r['truck']} - {r['driver']}: {r['total']} trips" for r in rows]
                rec.top_truck_driver = "\n".join(lines)

    @api.depends('filter_month', 'filter_year')
    def _compute_all_drivers_stats(self):
        for rec in self:
            start_date, end_date = rec._get_date_range()
            self.env.cr.execute("""
                        SELECT 
                            rp.name AS driver,
                            f.name AS truck,
                            COUNT(t.id) AS total_trips,
                            COALESCE(SUM(t.fuel_liters), 0) AS total_fuel
                        FROM trucking_planning_trip t
                        LEFT JOIN fleet_vehicle f ON f.id = t.truck_id
                        LEFT JOIN res_partner_driver rpd ON rpd.id = t.driver_id
                        LEFT JOIN res_partner rp ON rp.id = rpd.partner_id
                        WHERE t.status != 'cancelled'
                            AND t.plan_date >= %s
                            AND t.plan_date < %s
                            AND rpd.id IS NOT NULL
                        GROUP BY rp.name, f.name
                        ORDER BY total_trips DESC, rp.name
                    """, (start_date, end_date))

            rows = self.env.cr.dictfetchall()

            if not rows:
                rec.all_drivers_stats = "Không có dữ liệu."
            else:
                total_trips_sum = sum(r['total_trips'] for r in rows)
                total_fuel_sum = sum(r['total_fuel'] for r in rows)

                lines = []
                for r in rows:
                    driver = r['driver'] or 'N/A'
                    truck = r['truck'] or 'N/A'
                    trips = r['total_trips']
                    fuel = r['total_fuel']

                    line = f"{driver} - {truck}: {trips} chuyến, {fuel:.1f} lít"
                    lines.append(line)

                footer = f"\nTỔNG CỘNG: {total_trips_sum} chuyến, {total_fuel_sum:.1f} lít"

                rec.all_drivers_stats = "\n".join(lines) + footer

    def action_view_on_route_trips(self):
        """Mở view danh sách các trip đang on route"""
        self.ensure_one()
        start_date, end_date = self._get_date_range()

        return {
            'name': 'Trips On Route',
            'type': 'ir.actions.act_window',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'list,form',
            'domain': [
                ('plan_date', '>=', start_date),
                ('plan_date', '<', end_date),
                ('status', '=', 'on_route')
            ],
            'context': {'create': False},
            'target': 'current',
        }
