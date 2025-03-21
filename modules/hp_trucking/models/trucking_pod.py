from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PlaceOfDischarge(models.Model):
    _name = 'trucking.pod'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Place Of Discharge'
    _rec_name = 'pod_name'
    _order = 'write_date desc'

    pod_name = fields.Char(string='Place of Discharge', tracking=True)

    @api.model_create_multi  # This decorator allows batch creation
    def create(self, vals_list):
        records = super(PlaceOfDischarge, self).create(vals_list)
        for record in records:
            record._check_create_roadline_product()
        return records

    def _check_create_roadline_product(self):
        pols = self.env['trucking.pol'].search([])
        Roadline = self.env['trucking.roadline']
        Product = self.env['product.template']

        for pol in pols:
            roadline_name = f"{pol.pol_name} - {self.pod_name}"
            # Check if the sealine exists
            roadline = Roadline.search([('roadline_name', '=', roadline_name)], limit=1)

            if not roadline:
                # Create the sealine
                roadline = Roadline.create({
                    'pol_id': pol.id,
                    'pod_id': self.id,
                })

                # Create the product.template
                Product.create({
                    'type': 'trucking',
                    'roadline_id': roadline.id,
                    'name': roadline.roadline_name,
                    'categ_id': self.env.ref('product.product_category_all').id,  # ✅ Default category
                    'uom_id': self.env.ref('uom.product_uom_unit').id,  # ✅ Default Unit of Measure (Units)
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                })