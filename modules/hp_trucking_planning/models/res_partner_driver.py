from odoo import models, fields

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
    _sql_constraints = [
        ('unique_license_number', 'UNIQUE(license_number)','License Number must be unique!'),
    ]