from odoo import models, fields

class ResPartnerDriver(models.Model):
    _name = 'res.partner.driver'
    _description = 'Driver'
    _inherits = {'res.partner': 'driver_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    driver_id = fields.Many2one(
        comodel_name='res.partner',
        string='Info Driver',
        ondelete='cascade',
        required=True,
    )
    license_number = fields.Char(string='License Number', tracking=True)
    contract_date = fields.Date(string='Contract Date', tracking=True)
    vehicle_driver_history_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle.driver.history',
        inverse_name='driver_id',
    )

    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
    ]