from odoo import fields
from ..models.constants import WorkShiftType
from datetime import date, datetime, time, timedelta
import pytz
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class HrAttendanceService:
    _name = 'custom_component.partner.service'

    def __init__(self, env):
        self.env = env

    def get_total_time_attendace_by_employee(self, employee, date_from, date_to):
        work_shift_fixed = self.env['hr.work.shift'].search([('shift_type', '=', WorkShiftType.FIXED)], limit=1)
        work_shift_flexible = self.env['hr.work.shift'].search([('shift_type', '=', WorkShiftType.FLEXIBLE)], limit=1)
        
        work_shift = employee.work_shift_id
        if not work_shift:
            return {
                'days': 0.0,
                'hours': 0.0,
            }
        
        expected_hours = 8.0
        if work_shift_fixed:
            expected_hours = work_shift_fixed.fixed_end_time - work_shift_fixed.fixed_start_time
        
        attendances = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '!=', False),
            ('check_out', '!=', False),
            ('check_in', '>=', date_from),
            ('check_in', '<=', datetime.combine(date_to, time(23, 59, 59))),
        ])

        attendance_by_date = {}
        for att in attendances:
            date_key = att.check_in.date()
            if date_key not in attendance_by_date:
                attendance_by_date[date_key] = []
            attendance_by_date[date_key].append(att)

        work_hours = 0.0
        for date_key, records in attendance_by_date.items():
            first_in = min(r.check_in for r in records)
            last_out = max(r.check_out for r in records)
            if not (first_in and last_out):
                    continue

            first_in = self.datetime_to_float(fields.Datetime.context_timestamp(self.env.user, first_in))
            last_out = self.datetime_to_float(fields.Datetime.context_timestamp(self.env.user, last_out))
            
            if work_shift.shift_type == WorkShiftType.FIXED:
                if first_in > work_shift_fixed.fixed_end_time:
                    continue

                if first_in <= work_shift_fixed.fixed_start_time:
                    first_in = work_shift_fixed.fixed_start_time
                
                if last_out >= work_shift_fixed.fixed_end_time:
                    last_out = work_shift_fixed.fixed_end_time
                
                actual_hours = last_out - first_in
                if actual_hours >= 5:
                    actual_hours -= work_shift_fixed.break_time
            else:
                if first_in > work_shift_fixed.flexible_end_time:
                    continue

                if first_in <= work_shift_flexible.flexible_start_from:
                    first_in = work_shift_flexible.flexible_start_from
                
                if last_out >= work_shift_flexible.flexible_end_time:
                    last_out = work_shift_flexible.flexible_end_time

                actual_hours = last_out - first_in
                if actual_hours >= expected_hours + work_shift_flexible.break_time:
                    actual_hours = 8.0
                elif actual_hours >= 5:
                    actual_hours -= work_shift_fixed.break_time

            work_hours += actual_hours

        return {
            'days': round(work_hours / 8, 3),
            'hours': work_hours,
        }
    
    def datetime_to_float(self, dt):
        return round(dt.hour + dt.minute / 60.0 + dt.second / 3600.0, 2)