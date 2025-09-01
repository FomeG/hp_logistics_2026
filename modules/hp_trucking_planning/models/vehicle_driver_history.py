from odoo import models, fields, api

class VehicleDriverHistory(models.Model):

    _name = "trucking_planning.vehicle.driver.history"
    _description = "History of vehicle driver history"
    _order = "create_date desc"
    name = fields.Char(
        string='Name',
        compute='_compute_vehicle_driver_history_name',
        index=True,
        store=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        index=True,
    )
    driver_id = fields.Many2one(
        comodel_name='trucking_planning.driver',
        index=True,
    )
    start_date = fields.Date(
        string='Start date',
        required=True,
    )
    end_date = fields.Date(
        string='End date',
        index=True
    )
    _sql_constraints = [
        ('vehicle_open_unique', 'UNIQUE(vehicle_id) WHERE (end_date IS NULL OR end_date = False)', 'A vehicle can only have one open driver assignment at a time.')
    ]

    @api.depends('vehicle_id', 'driver_id')
    def _compute_vehicle_driver_history_name(self):
        for record in self:
            record.name = f"{record.driver_id.name} - {record.vehicle_id.name}"
