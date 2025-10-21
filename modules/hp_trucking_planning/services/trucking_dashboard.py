from odoo import models, fields, api
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TruckingDashboard(models.AbstractModel):
    _name = 'trucking.dashboard'
    _description = 'Trucking Dashboard Service'

    def _get_month_selection(self):
        return [(str(i), f'Tháng {i}') for i in range(1, 13)]

    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(str(year), str(year)) for year in range(current_year - 2, current_year + 2)]

    def _get_date_range(self, month=None, year=None):
        """Get date range for filtering"""
        if month and year:
            month = int(month)
            year = int(year)
        else:
            today = fields.Date.today()
            month = today.month
            year = today.year

        start_date = datetime(year, month, 1)
        end_date = start_date + relativedelta(months=1)

        return start_date, end_date

    def _get_selected_period(self, month, year):
        """Format selected period display"""
        if month and year:
            month_name = dict(self._get_month_selection()).get(month, '')
            return f"{month_name} {year}"
        return "Non-selected"

    def _compute_trip_statistics(self, month=None, year=None):
        """Compute all trip statistics for the given period"""
        Trip = self.env['trucking_planning.trip']
        start_date, end_date = self._get_date_range(month, year)

        base_domain = [
            ('plan_date', '>=', start_date),
            ('plan_date', '<', end_date),
        ]

        return {
            'total_trip_month': Trip.search_count(
                base_domain + [('status', '!=', 'cancelled')]
            ),
            'total_trip_done': Trip.search_count(
                base_domain + [('status', '=', 'done')]
            ),
            'total_trip_cancelled': Trip.search_count(
                base_domain + [('status', '=', 'cancelled')]
            ),
            'total_trip_on_route': Trip.search_count(
                base_domain + [('status', '=', 'on_route')]
            ),
            'total_trip_stopped': Trip.search_count(
                base_domain + [('status', '=', 'stopped')]
            ),
        }

    def _get_top_truck_driver(self, month=None, year=None):
        """Get top 5 truck-driver pairs by trip count"""
        start_date, end_date = self._get_date_range(month, year)

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
            return "No data available."

        lines = [f"{r['truck']} - {r['driver']}: {r['total']} trips" for r in rows]
        return "\n".join(lines)

    def _get_all_drivers_stats(self, month=None, year=None):
        """Get detailed statistics for all drivers"""
        start_date, end_date = self._get_date_range(month, year)

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
            return "Không có dữ liệu."

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
        return "\n".join(lines) + footer

    @api.model
    def get_dashboard_data(self, month=None, year=None):
        """
        Main service method: Return dashboard data as dictionary
        This is a pure service - no database records created
        """
        month = month or str(fields.Date.today().month)
        year = year or str(fields.Date.today().year)

        # Get all statistics
        trip_stats = self._compute_trip_statistics(month, year)

        return {
            'selected_period': self._get_selected_period(month, year),
            'filter_month': month,
            'filter_year': year,
            'total_trip_month': trip_stats['total_trip_month'],
            'total_trip_done': trip_stats['total_trip_done'],
            'total_trip_cancelled': trip_stats['total_trip_cancelled'],
            'total_trip_on_route': trip_stats['total_trip_on_route'],
            'total_trip_stopped': trip_stats['total_trip_stopped'],
            'top_truck_driver': self._get_top_truck_driver(month, year),
            'all_drivers_stats': self._get_all_drivers_stats(month, year),
        }