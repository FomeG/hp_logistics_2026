from odoo import models, fields


class ResPartnerInherit(models.AbstractModel):
    _inherit = ['res.partner']
    _description = 'Res Partner Inherit'

    partner_main_type_id = fields.Many2one(
        comodel_name='partner.main.type',
        string='Main Partner Type',
        index=True,
    )
    is_client = fields.Boolean(compute="_compute_is_client", store=True)

    def _compute_is_client(self):
        for rec in self:
            rec.is_client = rec.partner_main_type_id.code == 'shipping_line'
