from odoo import models, _
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = "product.category"

    def unlink(self):
        for category in self:
            product_count = self.env['product.template'].search_count([('categ_id', '=', category.id)])
            if product_count > 0:
                raise UserError(
                    _("Cannot delete category '%s' because there are still %d products in this category.") % (category.name, product_count)
                )
        return super().unlink()
