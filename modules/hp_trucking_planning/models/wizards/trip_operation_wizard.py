from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.hp_components.models import constants


class TripOperationWizard(models.TransientModel):
    _name = 'trucking_planning.trip.operation.wizard'
    _description = 'Wizard for Trip Operations'

    trip_id = fields.Many2one('trucking_planning.trip', required=True)
    operation = fields.Selection([
        (constants.TripStatus.ON_ROUTE, 'Start Trip (On Route)'),
        (constants.TripStatus.DONE, 'Mark Done'),
        (constants.TripStatus.STOPPED, 'Stopped'),
        (constants.TripStatus.CANCELLED, 'Cancelled'),
    ], required=True, string='Operation')
    operation_time = fields.Datetime(string="Time", default=fields.Datetime.now, required=True)
    note = fields.Text(string="Note")

    def action_confirm(self):
        self.ensure_one()
        trip = self.trip_id
        operation_map = {
            constants.TripStatus.ON_ROUTE: {'status': constants.TripStatus.ON_ROUTE, 'log': 'Trip started'},
            constants.TripStatus.DONE: {'status': constants.TripStatus.DONE, 'log': 'Trip marked Done'},
            constants.TripStatus.STOPPED: {'status': constants.TripStatus.STOPPED, 'log': 'Trip stopped'},
            constants.TripStatus.CANCELLED: {'status': constants.TripStatus.CANCELLED, 'log': 'Trip cancelled'},
        }
        if self.operation not in operation_map:
            raise UserError(_("Operation not found."))

        if self.operation == constants.TripStatus.CANCELLED and not self.note:
            raise ValidationError(_("Note is required when cancelling the trip."))

        trip.with_context(from_wizard=True)._set_status_via_wizard(self.operation, self.note)

        log_body = _(f"{operation_map[self.operation]['log']} at {self.operation_time}.\nNote: {self.note or ''}")
        trip.message_post(body=log_body)
        return {'type': 'ir.actions.act_window_close'}