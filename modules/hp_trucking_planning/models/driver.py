from odoo import models, fields


class Driver(models.Model):
    _name = 'trucking_planning.driver'
    _description = 'Driver'

    name = fields.Char(
        string='Name',
        required=True
    )
    phone_number = fields.Char(
        string='Phone Number',
    )
    cccd = fields.Char(
        string='CCCD',
        required=True,
    )
    license_number = fields.Char(
        required=True,
        string='License Number',
    )
    truck_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain="[('type', '=', 'truck')]",
        required=True,
    )
    truck_registration_date = fields.Date(
        related='truck_id.registration_date',
        readonly=True,
        string='Truck Registration Date',
    )
    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain="[('type', '=', 'trailer')]",
    )
    trailer_registration_date = fields.Date(
        related='trailer_id.registration_date',
        readonly=True,
        string='Trailer Registration Date',
    )
    contract_date = fields.Date(
        string='Contract Date',
    )
    notes = fields.Text(
        string='Notes',
    )

    plan_ids = fields.One2many(
        comodel_name='trucking_planning.plan',
        inverse_name='driver_id',
        string='Plans',
    )

    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
        ('unique_cccd', 'UNIQUE(cccd)', 'CCCD must be unique!'),
        ('unique_phone_number', 'UNIQUE(phone_number)', 'phone_number must be unique!'),
        ('unique_driver_truck_id', 'UNIQUE(truck_id)', 'Truck must be unique!'),
    ]

