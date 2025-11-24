from odoo import models, fields


class RouteBaseInherit(models.Model):
    _inherit = 'route.base'

    product_id = fields.Many2one(
        comodel_name='product.template',
        ondelete='cascade',
        store=True,
    )

