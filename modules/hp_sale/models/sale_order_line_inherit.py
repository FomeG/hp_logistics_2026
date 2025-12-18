from odoo import models, fields, api


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
        default=lambda self: self.env.company.currency_id
    )

    # 2. Giá gốc theo tiền tệ của dòng
    price_unit_original = fields.Float(
        string='Original Price',
        digits='Product Price',
        default=0.0
    )

    @api.onchange('product_id')
    def _onchange_product_id_set_currency(self):
        """Khi chọn sản phẩm, mặc định lấy tiền tệ của đơn hàng"""
        if not self.currency_id_line and self.order_id:
            self.currency_id_line = self.order_id.currency_id

    @api.onchange('price_unit_original', 'currency_id_line', 'order_id.currency_id', 'order_id.currency_rate')
    def _onchange_price_currency_conversion(self):
        """
        Logic cốt lõi (Updated):
        1. Line Currency -> Base Currency
        2. Base Currency -> Order Currency
        """
        # Lấy Base Currency (VND)
        base_currency = self.env['res.currency'].get_base_currency()

        for line in self:
            if not line.currency_id_line or not line.order_id.currency_id:
                continue

            # Case 1: Nếu Line Currency trùng với Order Currency -> Giữ nguyên
            if line.currency_id_line == line.order_id.currency_id:
                line.price_unit = line.price_unit_original
            else:
                # BƯỚC 1: Quy đổi Line Currency -> Base Currency (VND) ---
                # Sử dụng tỷ giá hệ thống cho bước này (vì Line Price Original là giá chuẩn đầu vào)
                amount_in_base = 0.0
                if line.currency_id_line == base_currency:
                    amount_in_base = line.price_unit_original
                else:
                    try:
                        # convert(amount, to_currency, company, date)
                        amount_in_base = line.currency_id_line._convert(
                            line.price_unit_original,
                            base_currency,
                            line.company_id or self.env.company,
                            line.order_id.date_order or fields.Date.today()
                        )
                    except Exception:
                        amount_in_base = line.price_unit_original

                # BƯỚC 2: Quy đổi Base Currency (VND) -> Order Currency (USD/...) ---
                # Sử dụng tỷ giá của đơn hàng (currency_rate) để đảm bảo khớp với Manual Rate
                # order.currency_rate được định nghĩa là: 1 Đơn vị Order Currency = X Đơn vị Base Currency
                # Ví dụ: Order là USD, Base là VND. Rate = 25,000.
                # Công thức: Amount_Order = Amount_Base / Rate
                order_rate = line.order_id.currency_rate
                if order_rate and order_rate > 0:
                    line.price_unit = amount_in_base / order_rate
                else:
                    line.price_unit = amount_in_base

    # Khi người dùng sửa tay price_unit (cột thành tiền quy đổi), update lại price_original tương ứng
    @api.onchange('price_unit')
    def _onchange_price_unit_reverse(self):
        for line in self:
            if line.currency_id_line == line.order_id.currency_id:
                line.price_unit_original = line.price_unit