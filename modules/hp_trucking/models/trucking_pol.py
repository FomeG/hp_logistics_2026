from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PlaceOfLoading(models.Model):
    _name = 'trucking.pol'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Place Of Loading'
    _rec_name = 'pol_name'
    _order = 'write_date desc'

    pol_name = fields.Char(string='Place Of Loading', tracking=True)

    @api.model_create_multi  # This decorator allows batch creation
    def create(self, vals_list):
        records = super(PlaceOfLoading, self).create(vals_list)
        for record in records:
            record._check_create_roadline_product()
        return records

    def _check_create_roadline_product(self):
        pods = self.env['trucking.pod'].search([])
        Roadline = self.env['trucking.roadline']
        Product = self.env['product.template']

        for pod in pods:
            roadline_name = f"{self.pol_name} - {pod.pod_name}"

            # Check if the sealine exists
            roadline = Roadline.search([('roadline_name', '=', roadline_name)], limit=1)

            if not roadline:
                # Create the sealine
                roadline = Roadline.create({
                    'pol_id': self.id,
                    'pod_id': pod.id,
                })

                # Create the product.template
                Product.create({
                    'type': 'trucking',
                    'roadline_id': roadline.id,
                    'name' : roadline.roadline_name,
                    'categ_id': self.env.ref('product.product_category_all').id,  # ✅ Default category
                    'uom_id': self.env.ref('uom.product_uom_unit').id,  # ✅ Default Unit of Measure (Units)
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                })