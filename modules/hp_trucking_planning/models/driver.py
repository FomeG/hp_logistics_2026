from odoo import models, fields


class Driver(models.Model):
    _name = 'trucking_planning.driver'
    _description = 'Driver'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
    )
    phone_number = fields.Char(
        string='Phone Number',
        tracking=True,
    )
    cccd = fields.Char(
        string='CCCD',
        required=True,
        tracking=True,
    )
    license_number = fields.Char(
        required=True,
        string='License Number',
        tracking=True,
    )
    contract_date = fields.Date(
        string='Contract Date',
        tracking=True,
    )
    notes = fields.Text(
        string='Notes',
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        string='Trips',
        inverse_name='driver_id',
    )
    vehicle_driver_history_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle.driver.history',
        inverse_name='driver_id',
    )

    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
        ('unique_cccd', 'UNIQUE(cccd)', 'CCCD must be unique!'),
        ('unique_phone_number', 'UNIQUE(phone_number)', 'phone_number must be unique!'),
    ]

