from odoo import models, fields, api
from ...hp_components.models import constants

class HrWorkShift(models.Model):
    _name = "hr.work.shift"
    _description = "Work Shift"

    name = fields.Char(string="Shift Name", required=True)
    shift_type = fields.Selection([
        (constants.WorkShiftType.FIXED, 'Fixed'),
        (constants.WorkShiftType.FLEXIBLE, 'Flexible'),
    ], string="Shift Type", required=True, default=constants.WorkShiftType.FIXED)

    # Fixed shift
    fixed_start_time = fields.Float(string="Start Time (Fixed)")
    fixed_end_time = fields.Float(string="End Time (Fixed)")

    # Flexible shift
    flexible_start_from = fields.Float(string="Start From (Flexible)")
    flexible_start_to = fields.Float(string="Start To (Flexible)")
    flexible_end_time = fields.Float(string="End Time (Flexible)")

    display_time = fields.Char(string="Work Time", compute="_compute_display_time")

    @api.depends(
        'shift_type', 'fixed_start_time', 'fixed_end_time',
        'flexible_start_from', 'flexible_start_to', 'flexible_end_time'
    )
    def _compute_display_time(self):
        for rec in self:
            def format_time(value):
                if not value:
                    return ''
                hours = int(value)
                minutes = int(round((value - hours) * 60))
                return f"{hours:02d}:{minutes:02d}"

            if rec.shift_type == constants.WorkShiftType.FIXED:
                rec.display_time = f"{format_time(rec.fixed_start_time)} - {format_time(rec.fixed_end_time)}"
            else:
                rec.display_time = (
                    f"From {format_time(rec.flexible_start_from)} to {format_time(rec.flexible_start_to)}, "
                    f"ends at {format_time(rec.flexible_end_time)}"
                )

    @api.onchange('shift_type')
    def _onchange_shift_type(self):
        if self.shift_type == constants.WorkShiftType.FIXED:
            self.flexible_start_from = self.flexible_start_to = self.flexible_end_time = False
        else:
            self.fixed_start_time = self.fixed_end_time = False
