from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PortOfLoading(models.Model):
    _name = 'pricing.pol'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Port Of Loading'
    _rec_name = 'pol_name'
    _order = 'write_date desc'

    pol_name = fields.Char(string='Port of Loading', tracking=True)

    @api.model_create_multi  # This decorator allows batch creation
    def create(self, vals_list):
        records = super(PortOfLoading, self).create(vals_list)
        for record in records:
            record._check_create_sealine_product()
        return records

    def _check_create_sealine_product(self):
        pods = self.env['pricing.pod'].search([])
        Sealine = self.env['pricing.sealine']
        Product = self.env['product.template']

        for pod in pods:
            sealine_name = f"{self.pol_name} - {pod.pod_name}"

            # Check if the sealine exists
            sealine = Sealine.search([('sealine_name', '=', sealine_name)], limit=1)

            if not sealine:
                # Create the sealine
                sealine = Sealine.create({
                    'pol_id': self.id,
                    'pod_id': pod.id,
                })

                # Create the product.template
                Product.create({
                    'type': 'pricing',
                    'sealine_id': sealine.id,
                    'name': sealine.sealine_name,
                    'categ_id': self.env.ref('product.product_category_all').id,  # ✅ Default category
                    'uom_id': self.env.ref('uom.product_uom_unit').id,  # ✅ Default Unit of Measure (Units)
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                })