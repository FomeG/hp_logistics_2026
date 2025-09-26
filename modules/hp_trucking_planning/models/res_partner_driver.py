from odoo import models, fields, api

class ResPartnerDriver(models.Model):
    _name = 'res.partner.driver'
    _description = 'Driver'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        index=True,
        required=True,
        ondelete='cascade',
    )

    # Computed field để lấy vehicle assignation history thông qua partner_id
    vehicle_assignation_history_ids = fields.One2many(
        comodel_name='fleet.vehicle.assignation.log',
        compute='_compute_vehicle_assignation_history',
        string='Vehicle Assignation History',
        readonly=True
    )
    license_number = fields.Char(
        string='License Number',
        index=True,
        tracking=True
    )
    license_issue_date = fields.Date(
        string='License Issue Date',
        tracking=True
    )
    license_expiry_date = fields.Date(
        string='License Expiry Date',
        tracking=True
    )
    license_type = fields.Selection([
        ('CE', 'CE'),
        ('FC', 'FC'),
        ('B2', 'B2'),
        ('C', 'C'),
        ],
        string='License Type',
        tracking=True
    )

    @api.depends('partner_id')
    def _compute_vehicle_assignation_history(self):
        for record in self:
            if record.partner_id:
                assignments = self.env['fleet.vehicle.assignation.log'].search([
                    ('driver_id', '=', record.partner_id.id)
                ])
                record.vehicle_assignation_history_ids = assignments
            else:
                record.vehicle_assignation_history_ids = False

    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
    ]