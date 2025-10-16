from odoo import models, fields ,api


class ResPartnerInherit(models.AbstractModel):
    _inherit = ['res.partner']
    _description = 'Res Partner Inherit'

    partner_main_type_id = fields.Many2one(
        comodel_name='partner.main.type',
        string='Main Partner Type',
        index=True,
    )
    is_shipping_line = fields.Boolean(compute="_compute_is_shipping_line", store=True)

    @api.depends('partner_main_type_id', 'partner_main_type_id.code')
    def _compute_is_shipping_line(self):
        for rec in self:
            rec.is_shipping_line = (rec.partner_main_type_id.code == 'shipping_line')

