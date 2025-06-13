from odoo import models, fields, api


class FreightPurchaseBookingLine(models.Model):
    _name = 'freight.purchase.booking.line'
    _description = 'Freight Booking Line'
    _inherit = ['mail.thread']

    booking_id = fields.Many2one('freight.purchase.booking', required=True, ondelete='cascade', string='Booking')
    #filter with perf reason
    pod_id = fields.Many2one(related='booking_id.quotation_id.route_id.pod_id',store=True,readonly=True,string='Port of Discharge (POD)')

    #keep ref with quotation line in order to track the price of    preorder vs order
    quotation_line_id = fields.Many2one('freight.purchase.quotation.line', required=True, string='Quotation Line')
    container_type_id = fields.Many2one(related='quotation_line_id.container_type_id',store=True,readonly=True, string='Container Type')

    # pre-order
    quantity = fields.Integer(string="quantity",required=True, default=1)
    price = fields.Float(string="This price should be the same as the one of quotation")
    sale_order_line_ids = fields.One2many('sale.order.line', 'booking_line_id', string='Sale Order Lines')
    reserved_by_id = fields.Many2one('res.users', string='Reserved by Salesperson')

    #these fields will be used for filter
    sale_order_id = fields.Many2one('sale.order', compute='_compute_sale_info', store=True, string='Sale Order')
    customer_id = fields.Many2one('res.partner', compute='_compute_sale_info', store=True, string='Customer')
    salesman_id = fields.Many2one('res.users', compute='_compute_sale_info', store=True, string='Salesperson')

    reservation_expiration_date = fields.Datetime(
        string='Reservation Expiry',
        help="Date after which the reservation is released if the sale order is not confirmed."
    )

    # Computed TEU
    teu_volume = fields.Float(compute='_compute_teu_volume', store=True, string='Teu Volume')
    history_ids = fields.One2many('freight.purchase.booking.line.history', 'booking_line_id')
    note = fields.Text()

    status = fields.Selection(
        string="Status",
        selection=[
            ('available', f"Available"),
            ('reserved', f"Reserved"),
            ('allocated', f"Allocated"),
            ('shipped', f"Shipped"),
            ('cancelled', f"Cancelled"),
        ],
        default='available',
        tracking=True,
        index=True,
        store=True,
    )

    @api.depends('sale_order_line_ids')
    def _compute_sale_info(self):
        for line in self:
            first_line = line.sale_order_line_ids[:1]
            if first_line:
                order = first_line.order_id
                line.sale_order_id = order.id
                line.customer_id = order.partner_id.id
                line.salesman_id = order.user_id.id
            else:
                line.sale_order_id = False
                line.customer_id = False
                line.salesman_id = False

    @api.depends('container_type_id', 'quantity')
    def _compute_teu_volume(self):
        for line in self:
            teu_ratio = line.container_type_id.teu
            line.teu_volume = teu_ratio * line.quantity

    @api.onchange('quotation_line_id')
    def _onchange_quotation_line_id(self):
        if self.quotation_line_id:
            self.price = self.quotation_line_id.price

