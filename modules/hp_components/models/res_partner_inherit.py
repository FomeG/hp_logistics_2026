from odoo import models, fields


class ResPartnerInherit(models.AbstractModel):
    _inherit = ['res.partner']
    _description = 'Res Partner Inherit'

    partner_main_type_id = fields.Many2one(
        comodel_name='partner.main.type',
        string='Main Partner Type',
        index=True,
        default=None,
        required=False
    )
