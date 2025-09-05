from odoo import models, fields, api , tools
from odoo.exceptions import ValidationError
from ..validators.shipping_line_validator import ShippingLineCreateValidator, ShippingLineUpdateValidator
import logging
_logger = logging.getLogger(__name__)

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

    # @tools.ormcache()
    def _get_shipping_line_contact_type(self):
        return self.env['partner.main.type'].search([('code', '=', 'shipping_line_contact')], limit=1)

    @api.model_create_multi
    def create(self, vals_list):
        shipping_line_type = self._get_shipping_line_type()
        if not shipping_line_type:
            raise ValidationError("Shipping line type not found. Please create it first.")
        shipping_line_contact_type = self._get_shipping_line_contact_type()

        for vals in vals_list:
            if shipping_line_type and not vals.get('partner_main_type_id') and not vals.get("parent_id"):
                vals['partner_main_type_id'] = shipping_line_type.id

        return super().create(vals_list)

    def write(self, vals):
        _logger.info("day la write")

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
            shipping_line_type = self._get_shipping_line_type()
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
    def process_set_shipping_line_type(self):
        shipping_line_type = self._get_shipping_line_type()
        shipping_line_contact_type = self._get_shipping_line_contact_type()

        for record in self:
            # 1. Nếu không có parent và chưa set type => shipping_line
            if not record.parent_id and not record.partner_main_type_id:
                record.partner_main_type_id = shipping_line_type

                # cập nhật con trong queue
                if shipping_line_contact_type:
                    for child in record.child_ids:
                        if child.partner_main_type_id != shipping_line_contact_type:
                            child.partner_main_type_id = shipping_line_contact_type

            # 2. Nếu có parent là shipping_line => set thành shipping_line_contact
            elif record.parent_id and record.parent_id.partner_main_type_id == shipping_line_type:
                if record.partner_main_type_id != shipping_line_contact_type:
                    record.partner_main_type_id = shipping_line_contact_type