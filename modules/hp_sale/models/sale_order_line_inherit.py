from odoo import models, fields, api
from odoo.tools import float_compare
from ...hp_components.models import constants
from odoo.exceptions import UserError

class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    res_model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model Source Id',
        index=True,
        ondelete='cascade',
        help="currently source can be truck or sea freight"
    )
    res_model = fields.Char(
        string='Model Source Name',
        index=True,
        related='res_model_id.model',
        precompute=True,
        store=True,
        readonly=True
    )
    res_id = fields.Many2oneReference(
        string='Record Source Id',
        index=True,
        model_field='res_model'
    )

    # 1. Tiền tệ của dòng (Mặc định lấy theo đơn hàng nếu không chọn)
    currency_id_line = fields.Many2one(
        'res.currency',
        string='Line Currency',
        compute='_compute_currency_id_line',
        store=True,
        precompute=True,
        default=lambda self: self.env.company.currency_id
    )

    # 2. Giá gốc theo tiền tệ của dòng
    price_unit_original = fields.Float(
        string='Price ',
        digits='Product Price',
        compute='_compute_price_unit_original',
        store=True,
        readonly=False,
        precompute=True
    )

    order_currency_rate = fields.Float(
        related='order_id.currency_rate',
        readonly=True,
        store=False
    )

    order_currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id',
        string='Order Currency',
        readonly=True,
        store=False
    )
    order_ref_currency_id = fields.Many2one(
        'res.currency',
        related='order_id.ref_currency_id',
        string='Order Ref Currency',
        readonly=True,
        store=False
    )

    price_list_price = fields.Float(
        string='Original Price',
        compute='_compute_price_list_price',
        digits='Product Price',
        store=False,
        help="Giá niêm yết gốc của sản phẩm trước khi áp dụng Pricelist"
    )

    @api.depends('product_id', 'product_uom_qty', 'order_id.pricelist_id')
    def _compute_price_unit_original(self):
        """Tự động tính giá gốc dựa trên Pricelist ngay khi dòng được tạo"""
        for line in self:
            # Nếu đang load demo data hoặc đã có giá trị từ onchange, không tính lại nếu không cần
            if not line.product_id:
                line.price_unit_original = 0.0
                continue

            pricelist = line.order_id.pricelist_id
            if not pricelist:
                line.price_unit_original = line.product_id.list_price
                continue

            qty = line.product_uom_qty or 1.0
            price = pricelist._get_product_price(line.product_id, qty, uom=line.product_uom)

            if price <= 0:
                product_currency = line.product_id.currency_id
                target_currency = pricelist.currency_id
                price = product_currency._convert(
                    line.product_id.list_price, target_currency,
                    line.company_id, line.order_id.date_order or fields.Date.today()
                )
            line.price_unit_original = price

    @api.depends('product_id', 'price_unit_original', 'currency_id_line', 'order_id.pricelist_id')
    def _compute_price_list_price(self):
        """Tính toán Giá niêm yết gốc từ Product Template, quy đổi về tiền tệ của dòng. Chỉ hiển thị nếu nó khác với giá thực tế đã áp dụng (price_unit_original)."""
        for line in self:
            if not line.product_id:
                line.price_list_price = 0.0
                continue

            # 1. Lấy giá niêm yết từ sản phẩm (Product Template)
            product_price = line.product_id.list_price
            product_currency = line.product_id.currency_id

            # 2. Quy đổi giá niêm yết đó về cùng loại tiền tệ với dòng hiện tại (currency_id_line)
            line_currency = line.currency_id_line or line.order_id.currency_id or line.env.company.currency_id

            original_price_in_line_currency = product_currency._convert(
                product_price,
                line_currency,
                line.company_id or line.env.company,
                line.order_id.date_order or fields.Date.today()
            )

            # So sánh với giá đã áp dụng (đã qua pricelist)
            prec = line_currency.rounding or 0.01
            if float_compare(line.price_unit_original, original_price_in_line_currency, precision_rounding=prec) != 0:
                line.price_list_price = original_price_in_line_currency
            else:
                # Nếu bằng nhau -> Ẩn
                line.price_list_price = 0.0

    @api.depends('product_id', 'order_id.pricelist_id', 'res_model_id', 'res_id')
    def _compute_currency_id_line(self):
        vnd = self.env.ref('base.VND')
        for line in self:
            currency = line._get_source_currency(vnd)
            line.currency_id_line = currency or line.order_id.pricelist_id.currency_id or line.company_id.currency_id

    def _get_source_currency(self, vnd):
        """Get currency from source record (freight items)."""
        self.ensure_one()
        if not (self.res_model_id and self.res_id):
            return False
        
        source = self.env[self.res_model].browse(self.res_id).exists()
        if not source:
            return False
        
        # route.base không có currency_id -> dùng VND
        if self.res_model == 'route.base':
            return vnd
        
        return source.currency_id if 'currency_id' in source._fields else False

    @api.depends('price_unit_original','currency_id_line','order_currency_rate','order_currency_id','order_ref_currency_id')
    def _compute_price_unit(self):
        """
        Tự động tính price_unit (giá hiển thị trong đơn hàng, thường là VND)
        dựa trên price_unit_original và cấu hình tỷ giá của Sale Order.
        """
        for line in self:
            if not line.order_id or not line.currency_id_line:
                line.price_unit = line.price_unit_original
                continue

            order_curr = line.order_id.currency_id
            line_curr = line.currency_id_line
            ref_curr = line.order_id.ref_currency_id
            current_rate = line.order_id.currency_rate or 1.0

            # Case 1: Nếu Line Currency trùng với Order Currency -> Giữ nguyên
            if line.currency_id_line == line.order_id.currency_id:
                line.price_unit = line.price_unit_original

            # Case 2: Dòng dùng tiền tham chiếu (ref_currency_id)
            # → nhân với tỷ giá đã cấu hình trên SO (1 Ref = X Base)
            elif ref_curr and line_curr.id == ref_curr.id:
                line.price_unit = line.price_unit_original * current_rate

            # Case 3: Dòng dùng tiền tệ khác → dùng hàm convert chuẩn của Odoo
            else:
                line.price_unit = line_curr._convert(
                    line.price_unit_original,
                    order_curr,  # chuyển về tiền của SO
                    line.company_id or self.env.company,
                    line.order_id.date_order or fields.Date.today()
                )

    @api.onchange('price_unit_original', 'currency_id_line', 'product_id')
    def _onchange_price_currency_conversion(self):
        self._compute_price_unit()

        # Khi chọn sản phẩm mới, mặc định currency theo đơn hàng nếu chưa có
        if self.product_id and not self.currency_id_line and self.order_id:
            self.currency_id_line = self.order_id.currency_id

    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def _onchange_product_id_set_price_from_pricelist(self):
        """Khi chọn sản phẩm hoặc thay đổi số lượng, tính lại giá"""
        for line in self:
            if not line.product_id or not line.order_id.pricelist_id:
                continue

            qty = line.product_uom_qty or 1.0
            uom = line.product_uom
            pricelist = line.order_id.pricelist_id

            # tìm quy tắc trong bảng
            price = pricelist._get_product_price(line.product_id, qty, uom=uom)

            # Nếu không khớp bất kỳ quy tắc nào trong bảng giá, lấy giá list_price của sản phẩm
            if price <= 0:
                # Quy đổi list_price từ tiền tệ sản phẩm sang tiền tệ của Pricelist
                product_currency = line.product_id.currency_id
                target_currency = pricelist.currency_id
                price = product_currency._convert(
                    line.product_id.list_price, target_currency,
                    line.company_id, fields.Date.today()
                )

            line.price_unit_original = price
            line.currency_id_line = pricelist.currency_id
            line._compute_price_unit()

    @api.onchange('price_unit_original', 'currency_id_line')
    def _onchange_price_unit_original(self):
        self._compute_price_unit()

    @api.onchange('price_unit')
    def _onchange_price_unit_reverse(self):
        """Nếu sửa trực tiếp price_unit (VND), cập nhật ngược lại giá gốc nếu cùng tiền tệ"""
        for line in self:
            # Chỉ đồng bộ ngược lại nếu giá VND > 0 và cùng loại tiền tệ
            if line.price_unit > 0 and line.currency_id_line == line.order_id.currency_id:
                line.price_unit_original = line.price_unit

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            order = self.env['sale.order'].browse(vals.get('order_id'))
            if order.state in constants.SaleOrderState.FORBIDDEN_STATES:
                raise UserError(
                    "You cannot add a sale order line when the order is in state %s"
                    % order.state
                )
        return super().create(vals_list)
    
    def unlink(self):
        orders = self.mapped('order_id')

        for line in self:
            if line.order_id.state in constants.SaleOrderState.FORBIDDEN_STATES:
                raise UserError(
                    "You cannot delete a sale order line when the order is in state %s"
                    % line.order_id.state
                )

        res = super().unlink()
        for order in orders:
            if not order.order_line:
                order.write({'state': constants.SaleOrderState.DRAFT}) 
        
        return res