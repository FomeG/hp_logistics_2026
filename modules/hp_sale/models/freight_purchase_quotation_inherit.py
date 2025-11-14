from odoo import models, fields
from odoo.exceptions import ValidationError

class FreightPurchaseQuotationInherit(models.Model):
    _inherit = 'freight.purchase.quotation'

    def _auto_create_product_selling_week(self):
        if not self.available_from or not self.available_to:
            return
        
        selling_week = self.env['selling.week'].create({
            'name': f"Selling Week From {self.available_from} - {self.available_to}",
            'start_date': self.available_from,
            'end_date': self.available_to,
            'is_active': False,
        })

        route = self.route_id
        if not route:
            return

        Product = self.env['product.template']
        product_template = Product.search([('route_id', '=', route.id)], limit=1)
        if not product_template:
            Product.with_context(create_from_route=True).create({
                'type': 'pricing',
                'route_id': route.id,
                'name': route.name,
                'categ_id': self.env.ref('product.product_category_all').id,
                'uom_id': self.env.ref('uom.product_uom_unit').id,
                'uom_po_id': self.env.ref('uom.product_uom_unit').id,
                'project_id': False,
                'project_template_id': False,
                'region_id': route.pol_id.region_id.id if route.pol_id.region_id else False,
            })
        else:
            product_template.write({
                'region_id': route.pol_id.region_id.id if route.pol_id.region_id else False,
            })

        product_selling_week = self.env['product.template.selling.week'].create({
            'goods_info': ' ',
            'selling_week_id': selling_week.id,
            'product_template_id': product_template.id,
        })
        if self.line_ids and self.shipping_line_id:
            values = []
            for quotation_line in self.line_ids:
                if quotation_line.container_type_id:
                    values.append({
                        'product_template_selling_week_id': product_selling_week.id,
                        'shipping_line_id': self.shipping_line_id.id,
                        'container_type_id': quotation_line.container_type_id.id,
                        'price': quotation_line.price,
                    })

            if values:
                self.env['product.template.selling.week.line'].create(values)

        return True