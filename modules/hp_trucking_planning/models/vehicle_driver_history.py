from odoo import models, fields


class VehicleDriverHistory(models.Model):

    _name = "trucking_planning.vehicle.driver.history"
    _description = "History of vehicle driver history"
    _order = "create_date desc"
    VEHICLE_DRIVER_HISTORY_ACTION_REMOVE = 'unassigned'
    VEHICLE_DRIVER_HISTORY_ACTION_ASSIGN = 'assigned'
    vehicle_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        index=True,
    )
    driver_id = fields.Many2one(
        comodel_name='trucking_planning.driver',
        index=True,
    )
    action = fields.Text(
        string='Action',
    )
