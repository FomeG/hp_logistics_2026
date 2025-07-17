from odoo import models, fields, api, exceptions
from ..validators.quotation_line_validator import QuotationLineValidator
import logging
_logger = logging.getLogger(__name__)
class FreightPurchaseQuotationLine(models.Model):
    _name = 'freight.purchase.quotation.line'
    _description = 'Purchase Quotation Line'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    name = fields.Char(
        string="Name",
        compute='_compute_name',
        store=False
    )
    quotation_id = fields.Many2one(
        comodel_name='freight.purchase.quotation',
        required=True,
        ondelete='cascade'
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        required=True
    )
    cost = fields.Float(
        string="Booking price",
        required=True
    )
    price = fields.Float(
        string="Internal price set by sale director",
        default=lambda self: self.cost if self.cost else 0.0
    )
    fee_line_ids = fields.One2many(
        comodel_name="freight.purchase.quotation.line.fee",
        inverse_name="quotation_line_id",
        string="Fee Lines"
    )

    @api.depends('quotation_id', 'container_type_id')
    def _compute_name(self):
        for record in self:
            if record.quotation_id and record.container_type_id:
                record.name = f"Quotation: {record.quotation_id.name} for container type: {record.container_type_id.name}"
            else:
                record.name = ''

    @api.model
    def create_from_booking_line_form(self, booking_line_form):
        try:
            validated, errors = QuotationLineValidator.validate_booking_line_form(booking_line_form, self.env)
            # Check required fields
            booking_id = booking_line_form.get('booking_id')
            if not booking_id:
                errors.append(f"Booking is required")
            booking = self.env['freight.purchase.booking'].browse(booking_id)
            if not booking.exists():
                errors.append(f"Booking #{booking_id} doesn't exist.")

            if errors:
                raise exceptions.ValidationError("\n".join([f"• {e}" for e in errors]))

            validated['quotation_id'] = booking.quotation_id.id

            return self.create(validated)
        except exceptions.ValidationError:
            raise  # Re-raise validation errors
        except Exception as e:
            _logger.exception(f"System error creating quotation line {e}")
            raise exceptions.ValidationError(f"A system error occurred, Cannot create quotation line. Please contact support.")

    @api.onchange('cost')
    def _onchange_cost(self):
        for record in self:
            if record.cost:
                record.price = record.cost

    @api.onchange('container_type_id')
    def _onchange_container_type_id(self):
        for line in self:
            default_ct_id = self.env.context.get('default_container_type_id')
            if default_ct_id and line.container_type_id and line.container_type_id.id != default_ct_id:
                raise exceptions.ValidationError('You can only select the container type passed from the quotation context')