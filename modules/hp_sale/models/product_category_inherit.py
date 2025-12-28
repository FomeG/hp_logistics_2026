from odoo import models, fields, _
from odoo.exceptions import UserError
from ...hp_components.models import constants

class ProductCategory(models.Model):
    _inherit = "product.category"
    _order = "id desc"
    # service_type = fields.Selection(
    #     constants.ProductCategoryServiceType.SELECT_OPTIONS,
    #     string="Service Type",
    #     default=constants.ProductCategoryServiceType.EXPORT,
    #     required=True,
    # )
    def action_show_category_products(self):
        self.ensure_one()
        return {
            'name': _('Products'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('categ_id', '=', self.id)],
            'context': {'default_categ_id': self.id},
            'target': 'current',
        }
