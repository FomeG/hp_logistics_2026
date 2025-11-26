from odoo import models, fields
from odoo.addons.hp_components.models import constants

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    is_monthly_billing = fields.Boolean(
        string="Monthly Billing",
        related='client_id.is_monthly_billing',
        readonly=False,
        store=True,
        help="If checked, CS order will be grouped into monthly batch orders. Can be overridden per sale order.",
    )
    cs_order_id = fields.Many2one(
        comodel_name='cs.order',
        string="CS Order",
        index=True,
    )