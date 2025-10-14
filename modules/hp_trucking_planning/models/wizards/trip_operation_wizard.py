from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class TripOperationWizard(models.TransientModel):
    _name = 'trucking_planning.trip.operation.wizard'
    _description = 'Wizard for Trip Operations'

    trip_id = fields.Many2one('trucking_planning.trip', required=True)
    operation = fields.Selection([
        ('on_route', 'Start Trip (On Route)'),
        ('done', 'Mark Done'),
        ('stopped', 'Stopped'),
        ('cancelled', 'Cancelled'),
    ], required=True, string='Operation')
    operation_time = fields.Datetime(string="Time", default=fields.Datetime.now, required=True)
    note = fields.Text(string="Note")

    def action_confirm(self):
        self.ensure_one()
        trip = self.trip_id
        operation_map = {
            'on_route': {'status': 'on_route', 'log': 'Trip started'},
            'done': {'status': 'done', 'log': 'Trip marked Done'},
            'stopped': {'status': 'stopped', 'log': 'Trip stopped'},
            'cancelled': {'status': 'cancelled', 'log': 'Trip cancelled'},
        }
        if self.operation not in operation_map:
            raise UserError(_("Operation not found."))

        if self.operation == 'cancel' and not self.note:
            raise ValidationError(_("Note is required when cancelling the trip."))

        trip.with_context(from_wizard=True)._set_status_via_wizard(self.operation, self.note)

        log_body = _(f"{operation_map[self.operation]['log']} at {self.operation_time}.\nNote: {self.note or ''}")
        trip.message_post(body=log_body)
        return {'type': 'ir.actions.act_window_close'}