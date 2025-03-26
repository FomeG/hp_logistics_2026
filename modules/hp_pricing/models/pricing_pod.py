from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

import logging

_logger = logging.getLogger(__name__)

class PortOfDischarge(models.Model):
    _name = 'pricing.pod'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Port Of Discharge'
    _rec_name = 'pod_name'
    _order = 'write_date desc'

    pod_name = fields.Char(string='Port of Discharge', tracking=True)
    region_id = fields.Many2one(
        'pricing.region', string='Region', tracking=True)

    @api.model
    def default_get(self, fields_list):
        res = super(PortOfDischarge, self).default_get(fields_list)
        user = self.env.user

        # Check if the user has a region assigned
        if 'region_id' in fields_list and user.region_id:
            res['region_id'] = user.region_id.id

        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PortOfDischarge, self).create(vals_list)
        for record in records:
            record._check_create_sealine_product()
        return records

    def _check_create_sealine_product(self):
        pols = self.env['pricing.pol'].search([])
        Sealine = self.env['pricing.sealine']
        Product = self.env['product.template']

        for pol in pols:
            sealine_name = f"{pol.pol_name} - {self.pod_name}"
            # Check if the sealine exists
            sealine = Sealine.search([('sealine_name', '=', sealine_name)], limit=1)

            if not sealine:
                # Create the sealine
                sealine = Sealine.create({
                    'pol_id': pol.id,
                    'pod_id': self.id,
                })

                # Create the product.template
                Product.create({
                    'type': 'pricing',
                    'sealine_id': sealine.id,
                    'name': sealine.sealine_name,
                    'categ_id': self.env.ref('product.product_category_all').id,  # ✅ Default category
                    'uom_id': self.env.ref('uom.product_uom_unit').id,  # ✅ Default Unit of Measure (Units)
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                    'project_id': False,
                    'project_template_id': False,
                })