from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class TripOperationWizard(models.TransientModel):
    _name = 'trucking_planning.trip.operation.wizard'
    _description = 'Wizard for Trip Operations'

    trip_id = fields.Many2one('trucking_planning.trip', required=True)
    operation = fields.Char(required=True)
    operation_time = fields.Datetime(string="Time", default=fields.Datetime.now, required=True)
    note = fields.Text(string="Note")

    def action_confirm(self):
        self.ensure_one()
        trip = self.trip_id
        operation_map = {
            'start': {'status': 'in_progress', 'log': 'Trip started'},
            'stop': {'status': 'stopped', 'log': 'Trip stopped'},
            'end': {'status': 'done', 'log': 'Trip ended'},
            'cancel': {'status': 'cancelled', 'log': 'Trip cancelled'},
        }
        if self.operation not in operation_map:
            raise UserError(_("Operation not found."))

        if self.operation == 'cancel' and not self.note:
            raise ValidationError(_("Note is required when cancelling the trip."))

        new_status = operation_map[self.operation]['status']
        trip.status = new_status

        log_body = _(f"{operation_map[self.operation]['log']} at {self.operation_time}.\nNote: {self.note or ''}")
        trip.message_post(body=log_body)

        return {'type': 'ir.actions.act_window_close'}