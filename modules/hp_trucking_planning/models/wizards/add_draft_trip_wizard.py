from odoo import models, fields, api
from odoo.exceptions import UserError


class AddDraftTripWizard(models.TransientModel):
    _name = 'trucking_planning.add_draft_trip.wizard'
    _description = 'Add Draft Trip Wizard'

    plan_line_id = fields.Many2one('trucking_planning.plan.line', required=True)
    number_of_trips = fields.Integer(string="Number of Trips", default=1, required=True, help="Enter the number of trips (trucks) to create. The trips (trucks) will be created with the 'Draft' status.")

    def action_confirm(self):
        if self.number_of_trips <= 0:
            raise UserError("Number of trips must be greater than 0.")

        self.plan_line_id.with_delay()._create_draft_trips(self.number_of_trips)

        return {'type': 'ir.actions.act_window_close'}