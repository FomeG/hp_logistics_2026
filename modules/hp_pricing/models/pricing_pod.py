from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

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
        elif not user.region_id and user.has_group('hp_pricing.group_hp_pricing_member'):
            raise UserError(_("The current user is not assigned to a region yet."))
        return res

    @api.constrains('pod_name')
    def _check_unique_pod_name(self):
        """ Ensure unique pod_name """
        for record in self:
            existing_pod = self.env['pricing.pod'].search([
                ('pod_name', '=', record.pod_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_pod:
                raise ValidationError(_("The Port of Discharge name '%s' already exists.") % record.pod_name)

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
                Product.with_context(create_from_pol_pod=True).create({
                    'type': 'pricing',
                    'sealine_id': sealine.id,
                    'name': sealine.sealine_name,
                    'categ_id': self.env.ref('product.product_category_all').id,  # ✅ Default category
                    'uom_id': self.env.ref('uom.product_uom_unit').id,  # ✅ Default Unit of Measure (Units)
                    'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                })

    def write(self, vals):
        """ Update sealine and product when POD name is changed """
        result = super(PortOfDischarge, self).write(vals)

        if 'pod_name' in vals:
            for record in self:
                record._update_sealine_product()

        return result

    def _update_sealine_product(self):
        """ Update sealine and related products when POD name changes """
        Sealine = self.env['pricing.sealine']
        Product = self.env['product.template']

        sealines = Sealine.search([('pod_id', '=', self.id)])

        for sealine in sealines:
            new_sealine_name = f"{sealine.pol_id.pol_name} - {self.pod_name}"
            sealine.write({'sealine_name': new_sealine_name})

            products = Product.search([('sealine_id', '=', sealine.id)])
            products.write({'name': new_sealine_name})