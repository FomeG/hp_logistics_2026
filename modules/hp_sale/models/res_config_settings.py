# -*- coding: utf-8 -*-
from odoo import api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.model
    def _auto_enable_pricelist(self):
        group_pricelist = self.env.ref('product.group_product_pricelist', raise_if_not_found=False)
        group_user = self.env.ref('base.group_user', raise_if_not_found=False)

        if group_pricelist and group_user and group_pricelist not in group_user.implied_ids:
            group_user.write({
                'implied_ids': [(4, group_pricelist.id)]
            })

        return True