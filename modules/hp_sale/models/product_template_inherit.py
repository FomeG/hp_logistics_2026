from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

class ProductTemplate(models.Model):
    _inherit = "product.template"

    route_id = fields.Many2one(
        'route.base',
        string='Route',
        tracking=True,
        help="The route is used for freight type",
        ondelete='cascade',
    )
    type = fields.Selection(
        constants.ProductTemplateType.SELECT_OPTIONS,
        required=True,
        default=constants.ProductTemplateType.SEA_FREIGHT
    )

    product_type = fields.Selection(
        constants.ProductTemplateType.SELECT_OPTIONS,
        string='HP Product Type',
        tracking=True,
        help="Product type for HP Logistics system"
    )

    # Field hiển thị cho user khi tạo mới/edit - chỉ Custom và Services
    product_type_editable = fields.Selection(
        selection=[
            (constants.ProductTemplateType.CUSTOM, 'Custom'),
            (constants.ProductTemplateType.SERVICES, 'Services'),
        ],
        string='Product Type',
        compute='_compute_product_type_editable',
        inverse='_inverse_product_type_editable',
        store=False,
        required=False,
    )

    # Field hiển thị cho user khi xem - tất cả 4 loại
    product_type_display = fields.Selection(
        selection=constants.ProductTemplateType.SELECT_OPTIONS,
        string='Product Type',
        compute='_compute_product_type_display',
        inverse='_inverse_product_type_display',
        store=False,
        required=False,
    )

    @api.depends('product_type')
    def _compute_product_type_editable(self):
        for record in self:
            if record.product_type in [constants.ProductTemplateType.CUSTOM, constants.ProductTemplateType.SERVICES]:
                record.product_type_editable = record.product_type

    def _inverse_product_type_editable(self):
        for record in self:
            record.product_type = record.product_type_editable
            record.type = record.product_type_editable

    @api.depends('product_type')
    def _compute_product_type_display(self):
        for record in self:
            # Hiển thị tất cả 4 loại: SEA_FREIGHT, TRUCK_FREIGHT, CUSTOM, SERVICES
            record.product_type_display = record.product_type

    def _inverse_product_type_display(self):
        for record in self:
            record.product_type = record.product_type_display
            record.type = record.product_type_display

    # def _inverse_product_type_display(self):
    #     """Lưu giá trị từ product_type_display vào field product_type"""
    #     for record in self:
    #         if record.product_type_display == constants.ProductTemplateType.SERVICES:
    #             record.product_type = constants.ProductTemplateType.SERVICES
    #             # Đồng thời set type gốc của Odoo
    #             record.type = constants.ProductTemplateType.SERVICES  # 'services'
    #         elif record.product_type_display == constants.ProductTemplateType.CUSTOM:
    #             record.product_type = constants.ProductTemplateType.CUSTOM
    #             # Đồng thời set type gốc của Odoo
    #             record.type = constants.ProductTemplateType.CUSTOM  # 'custom'

    complete_time = fields.Float(
        string="Thời gian hoàn thành (s)",
        digits=(3, 1),
        help="Thời gian hoàn thành dịch vụ"
    )

    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        tracking=True
    )

    is_editable = fields.Boolean(
        string="Is Editable By Salesman",
        compute='_compute_is_editable',
        store=False,
        help="Technical field to check if current user can edit this product"
    )

    def _compute_is_editable(self):
        user_service = self.env['hp_components.user.service']
        allowed_types = [
            constants.ProductTemplateType.CUSTOM,
            constants.ProductTemplateType.SERVICES
            ]
        for record in self:
            if record.type not in allowed_types:
                record.is_editable = False
            else:
                record.is_editable = user_service.is_salesman_manager() or user_service.is_salesman_leader() or user_service.is_admin_user()

    def action_sale_order_add_selected_lines(self):
        sale_order_id = self.env.context.get('sale_order_id')
        lines = self
        if not sale_order_id or not lines:
            raise ValidationError("No Sale Order or selected lines found.")

        values = []
        for line in lines:
            values.append({
                'name': line.name,
                'order_id': sale_order_id,
                'product_id': line.product_variant_id.id,
                'product_uom_qty': 1.0,
                'price_unit': line.list_price,
            })

        self.env['sale.order.line'].sudo().create(values)
        return True
