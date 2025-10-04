from odoo import models, api, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_id = fields.Many2one(
        comodel_name='hr.branch',
        string='Sales Branch',
        index=True,
    )
