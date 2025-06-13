from odoo import models, fields, api
from odoo.exceptions import ValidationError


class FreightPurchaseBooking(models.Model):

    _name = 'freight.purchase.booking'
    _description = 'Freight Purchase Booking'
    _inherit = ['mail.thread','unique.code.mixin']
    name = fields.Char(required=True, string='Booking Name')
    vessel_id = fields.Many2one('freight.purchase.vessel')
    quotation_id = fields.Many2one('freight.purchase.quotation', required=True)
    etd = fields.Date(required=True,index=True)
    status = fields.Selection(
        string="Status",
        selection=[
            ('draft', f'Draft'),
            ('pending', f'Pending'),
            ('confirmed', f'Confirmed'),
            ('fully_assigned', f'Fully Assigned'),
            ('shipped', f'Shipped'),
            ('cancelled', f'Cancelled'),
            ('expired', f'Expired'),
        ],
        default='confirmed',
        tracking=True,
        index=True,
        store=True,
    )
    #duplication for the perf reason
    route_id = fields.Many2one(related='quotation_id.route_id', store=True)
    shipping_line_id = fields.Many2one(related='quotation_id.shipping_line_id', store=True)
    teu_volume = fields.Float()
    note = fields.Text()
    line_ids = fields.One2many('freight.purchase.booking.line', 'booking_id', string='Booking Lines')


    @api.constrains('code')
    def _check_code_required_and_unique(self):
        for record in self:
            if not record.code:
                raise ValidationError("Code is required.")
            existing = self.search([
                ('code', '=', record.code),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(f"Booking code '{record.code}' already exists.")
