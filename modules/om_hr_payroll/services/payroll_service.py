from odoo import fields
from datetime import datetime, time, timedelta

class PayrollService:
    _name = 'payroll.service'

    def __init__(self, env):
        self.env = env

    def calculate_work_time(self, contract, date_from, date_to):
        weekly_hours = contract.resource_calendar_id.full_time_required_hours
        daily_hours = contract.resource_calendar_id.hours_per_day

        full_days = int(weekly_hours // daily_hours)
        remainder = weekly_hours - full_days * daily_hours
        partial_fraction = remainder / daily_hours if daily_hours else 0.0
        partial_weekday = full_days if (partial_fraction > 0 and full_days < 7) else None

        total_days = 0.0
        total_hours = 0.0
        cur = date_from
        details = []
        while cur <= date_to:
            wd = cur.weekday()
            if wd < full_days:
                added_days, added_hours = 1.0, daily_hours
            elif partial_weekday is not None and wd == partial_weekday:
                added_days, added_hours = partial_fraction, partial_fraction * daily_hours
            else:
                added_days, added_hours = 0.0, 0.0

            if added_days:
                details.append((cur.isoformat(), added_days, added_hours))

            total_days += added_days
            total_hours += added_hours
            cur += timedelta(days=1)

        return {
            "days": total_days,
            "hours": total_hours,
            "details": details,
        }

    def get_total_time_paid_by_employee(self, employee, date_from, date_to):
        time_offs = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('request_date_from', '>=', date_from),
            ('request_date_to', '<=', date_to),
            ('number_of_days', '!=', 0),
            ('number_of_hours', '!=', 0),
            ('overtime_id', '=', False),
            ('state', '=', 'validate'),
            ('holiday_status_id.unpaid', '=', False),
        ])

        if not time_offs:
            return {
                'days': 0.0,
                'hours': 0.0,
            }

        return {
            'days': sum(time_offs.mapped('number_of_days')),
            'hours': sum(time_offs.mapped('number_of_hours')),
        }

    def get_total_time_unpaid_by_employee(self, employee, date_from, date_to):
        time_offs = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('request_date_from', '>=', date_from),
            ('request_date_to', '<=', date_to),
            ('number_of_days', '!=', 0),
            ('number_of_hours', '!=', 0),
            ('overtime_id', '=', False),
            ('state', '=', 'validate'),
            ('holiday_status_id.unpaid', '=', True),
        ])

        if not time_offs:
            return {
                'days': 0.0,
                'hours': 0.0,
            }

        return {
            'days': sum(time_offs.mapped('number_of_days')),
            'hours': sum(time_offs.mapped('number_of_hours')),
        }