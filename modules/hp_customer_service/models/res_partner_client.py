from odoo import models, fields, api


class ResPartnerClient(models.Model):
    _inherit = ['res.partner.client']

    is_monthly_billing = fields.Boolean(
        string="Monthly Billing",
        default=False,
        help="If checked, CS orders from this client will be grouped into monthly batch orders",
        tracking=True,
    )