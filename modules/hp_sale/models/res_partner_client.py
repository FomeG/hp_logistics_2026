from odoo import models, fields

class ResPartnerClient(models.Model):
    _name = 'res.partner.client'
    _description = 'Partner Client'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Info Client',
        ondelete='cascade',
        required=True,
    )
    