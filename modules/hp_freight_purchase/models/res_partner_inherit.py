from odoo import models, fields, api , tools
from odoo.exceptions import ValidationError
from ..validators.shipping_line_validator import ShippingLineCreateValidator, ShippingLineUpdateValidator

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    _order = 'create_date desc'

    booking_ids = fields.One2many('freight.purchase.booking', 'shipping_line_id', string='Bookings')
    quotation_ids = fields.One2many('freight.purchase.quotation', 'shipping_line_id', string='Quotations')

    total_bookings = fields.Char(string="Total Bookings", compute='_compute_total_booking', store=False)
    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)
    @tools.ormcache()
    def _get_shipping_line_type(self):
        return self.env['partner.main.type'].search([('code', '=', 'shipping_line')], limit=1)


    @api.model_create_multi
    def create(self, vals_list):
        shipping_line_type = self._get_shipping_line_type()
        if not shipping_line_type:
            raise ValidationError("Shipping line type not found. Please create it first.")

        for vals in vals_list:
            if shipping_line_type and not vals.get('partner_main_type_id'):
                vals['partner_main_type_id'] = shipping_line_type.id

            if self._is_shipping_line_partner(vals):
                validated, errors = ShippingLineCreateValidator.validate(vals, self.env)
                if errors:
                    raise ValidationError("\n".join([f"• {e}" for e in errors]))

        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            if self._is_shipping_line_partner(vals, record):
                validated, errors = ShippingLineUpdateValidator.validate(vals, self.env)
                if errors:
                    raise ValidationError("\n".join([f"• {e}" for e in errors]))

        return super().write(vals)

    def _is_shipping_line_partner(self, vals, record=None):
        """Check if the partner is a shipping line based on partner_main_type_id"""
        if record:
            # For write operation, check if the partner is becoming a shipping line
            partner_main_type_id = vals.get('partner_main_type_id', record.partner_main_type_id.id)
        else:
            # For create operation, check the vals
            partner_main_type_id = vals.get('partner_main_type_id')

        if partner_main_type_id:
            # Search for shipping line type by code instead of using env.ref
            shipping_line_type = self.env['partner.main.type'].search([
                ('code', '=', 'shipping_line')
            ], limit=1)
            return shipping_line_type and partner_main_type_id == shipping_line_type.id
        return False

    @api.depends('booking_ids')
    def _compute_total_booking(self):
        for record in self:
            if record.booking_ids:
                total = len(record.booking_ids)
                record.total_bookings = f"{total} Booking(s)"
            else:
                record.total_bookings = "0 Booking(s)"

    @api.depends('quotation_ids')
    def _compute_total_quotation(self):
        for record in self:
            if record.quotation_ids:
                total = len(record.quotation_ids)
                record.total_quotations = f"{total} Quotation(s)"
            else:
                record.total_quotations = "0 Quotation(s)"

    #todo require name + email