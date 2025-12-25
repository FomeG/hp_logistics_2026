from odoo import models, fields, api
from odoo.odoo.tools import float_compare


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
        default=lambda self: self.env.company.currency_id
    )

    # 2. Giá gốc theo tiền tệ của dòng
    price_unit_original = fields.Float(
        string='Original Price',
        digits='Product Price',
        default=0.0,
        store = True
    )

    order_currency_rate = fields.Float(
        related='order_id.currency_rate',
        readonly=True,
        store=False
    )

    order_currency_id = fields.Many2one(
        'res.currency',
        related='order_id.currency_id',
        readonly=True,
        store=False
    )
    order_ref_currency_id = fields.Many2one(
        'res.currency',
        related='order_id.ref_currency_id',
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

    @api.depends('product_id', 'price_unit_original', 'currency_id_line', 'order_id.pricelist_id')
    def _compute_price_list_price(self):
        """Tính toán Giá niêm yết gốc từ Product Template, quy đổi về tiền tệ của dòng. Chỉ hiển thị nếu nó khác với giá thực tế đã áp dụng (price_unit_original)."""
        for line in self:
            if not line.product_id:
                line.price_list_price = 0.0
                continue

            product_price = line.product_id.list_price
            product_currency = line.product_id.currency_id
            line_currency = line.currency_id_line or line.order_id.currency_id or line.env.company.currency_id

            # 3. Quy đổi giá niêm yết từ tiền tệ của Product sang tiền tệ của dòng
            original_price_in_line_currency = product_currency._convert(
                product_price,
                line_currency,
                line.company_id or line.env.company,
                line.order_id.date_order or fields.Date.today()
            )

            # So sánh với giá đã áp dụng (đã qua pricelist)
            prec = line_currency.rounding or 0.01

            # Nếu giá gốc khác giá đã áp dụng (do pricelist làm thay đổi) -> Hiện giá gốc
            if float_compare(line.price_unit_original, original_price_in_line_currency, precision_rounding=prec) != 0:
                line.price_list_price = original_price_in_line_currency
            else:
                # Nếu bằng nhau -> Ẩn
                line.price_list_price = 0.0

    @api.depends('product_id', 'order_id.pricelist_id')
    def _compute_currency_id_line(self):
        for line in self:
            if line.order_id.pricelist_id:
                line.currency_id_line = line.order_id.pricelist_id.currency_id
            else:
                line.currency_id_line = line.company_id.currency_id

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

            current_rate = line.order_id.currency_rate or 1.0

            # Case 1: Nếu Line Currency trùng với Order Currency -> Giữ nguyên
            if line.currency_id_line == line.order_id.currency_id:
                line.price_unit = line.price_unit_original

            # Case 2: Dòng dùng tiền tham chiếu (ref_currency_id)
            # → nhân với tỷ giá đã cấu hình trên SO (1 Ref = X Base)
            elif line.currency_id_line == line.order_id.ref_currency_id:
                line.price_unit = line.price_unit_original * current_rate

            # Case 3: Dòng dùng tiền tệ khác → dùng hàm convert chuẩn của Odoo
            else:
                line.price_unit = line.currency_id_line._convert(
                    line.price_unit_original,
                    line.order_id.currency_id,  # chuyển về tiền của SO
                    line.company_id or self.env.company,
                    line.order_id.date_order or fields.Date.today()
                )

    @api.onchange('price_unit_original', 'currency_id_line', 'product_id')
    def _onchange_price_currency_conversion(self):
        self._compute_price_unit()

        # Khi chọn sản phẩm mới, mặc định currency theo đơn hàng nếu chưa có
        if self.product_id and not self.currency_id_line and self.order_id:
            self.currency_id_line = self.order_id.currency_id

    @api.onchange('price_unit')
    def _onchange_price_unit_reverse(self):
        for line in self:
            if line.currency_id_line and line.order_id and line.currency_id_line == line.order_id.currency_id:
                line.price_unit_original = line.price_unit

    @api.onchange('product_id', 'product_uom', 'product_uom_qty')
    def _onchange_product_id_set_price_from_pricelist(self):
        """Khi chọn sản phẩm, lấy giá từ Pricelist của đơn hàng gán vào price_unit_original"""
        if not self.product_id or not self.order_id.pricelist_id:
            return

        # Lấy giá từ Pricelist dựa trên số lượng và đơn vị tính
        price = self.order_id.pricelist_id._get_product_price(
            self.product_id,
            self.product_uom_qty or 1.0,
            uom=self.product_uom
        )

        self.price_unit_original = price
        self.currency_id_line = self.order_id.pricelist_id.currency_id
        self._compute_price_unit()

    @api.onchange('price_unit_original', 'currency_id_line')
    def _onchange_price_unit_original(self):
        self._compute_price_unit()

    @api.onchange('price_unit')
    def _onchange_price_unit_reverse(self):
        """Nếu sửa trực tiếp price_unit (VND), cập nhật ngược lại giá gốc nếu cùng tiền tệ"""
        for line in self:
            if line.currency_id_line and line.order_id and line.currency_id_line == line.order_id.currency_id:
                line.price_unit_original = line.price_unit