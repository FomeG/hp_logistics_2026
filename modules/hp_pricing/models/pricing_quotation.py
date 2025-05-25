from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

class PricingQuotation(models.Model):
    _name = 'pricing.quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Quotation'
    _rec_name = 'display_name'
    _order = 'write_date desc'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    cont_20_price = fields.Float('Cont 20 Price', tracking=True)
    cont_40_price = fields.Float('Cont 40 Price', tracking=True)

    fee_type = fields.Selection(selection=[
        ('SBJ', 'SBJ'),
        ('Allin', 'Allin'),
    ], string='Booking Fee Type', default='Allin', tracking=True)

    sealine_id = fields.Many2one(
        'pricing.sealine', string="Sealine",
        tracking=True
    )

    current_volume_total = fields.Integer(string='Total Current Volume (TEU)', compute='_compute_volume_total', store=True)

    valid_from = fields.Date(
        string="Valid From",
    )
    valid_to = fields.Date(
        string="Valid To",
    )

    booking_ids = fields.One2many(
        'pricing.booking',
        'pricing_quotation_id',
        string="Bookings"
    )

    # One2many field to see all sales order lines using this booking
    sale_line_ids = fields.One2many(
        'sale.order.line',
        'pricing_quotation_id',
        string="Sales Order Lines",
        copy=False
    )

    active = fields.Boolean(default=True)
    always = fields.Boolean("Always Valid", default=False)

    # Computed fields for TEU tracking from sale orders
    reserved_teu_from_orders = fields.Float(
        string="Reserved TEU from Orders",
        compute="_compute_order_teu_usage",
        store=True,
        help="Total TEU reserved by sale order lines in state 'sale'"
    )

    quotation_teu_warning_message = fields.Html(
        string="Quotation TEU Usage",
        compute="_compute_quotation_teu_warning",
        store=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        # Create the quotation first
        quotations = super().create(vals_list)

        project_task_id = self._context.get('default_project_task_id')
        if project_task_id:
            project_task = self.env['project.task'].browse(project_task_id)
            if project_task.exists():
                project_task.pricing_quotation_id = quotations[0].id

        # Auto-link unlinked bookings with same fee_type
        # for quotation in quotations:
        #     quotation._auto_link_bookings()

        return quotations

    def write(self, vals):
        result = super().write(vals)

        # Check if fee_type changed and re-link bookings
        # if 'fee_type' in vals:
        #     for record in self:
        #         record._auto_link_bookings()

        return result

    # def _auto_link_bookings(self):
    #     """Automatically link bookings with same fee_type that are not linked to any quotation"""
    #     unlinked_bookings = self.env['pricing.booking'].search([
    #         ('fee_type', '=', self.fee_type),
    #         ('pricing_quotation_id', '=', False),
    #         ('active', '=', True)
    #     ])
    #
    #     if unlinked_bookings:
    #         unlinked_bookings.sudo().write({'pricing_quotation_id': self.id})

    def action_create_booking(self):
        self.ensure_one()
        return {
            'name': _('Create Booking'),
            'type': 'ir.actions.act_window',
            'res_model': 'pricing.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fee_type': self.fee_type,
                'create_booking_from_quotation': True,
                'quotation_id': self.id,
                # Set default voyage based on sealine if available
                'default_voyage_id': self._get_default_voyage_for_sealine(),
            }
        }

    def _get_default_voyage_for_sealine(self):
        """Get a default voyage for the sealine of this quotation"""
        if self.sealine_id:
            voyage = self.env['pricing.voyage'].search([
                ('sealine_id', '=', self.sealine_id.id)
            ], limit=1)
            return voyage.id if voyage else False
        return False

    # display_name
    @api.depends('fee_type', 'valid_from', 'valid_to', 'always', 'sealine_id')
    def _compute_display_name(self):
        for record in self:
            sealine_name = record.sealine_id.sealine_name if record.sealine_id else "No Sealine"
            if record.always:
                record.display_name = f"{sealine_name} - {record.fee_type} (Always Valid)"
            else:
                valid_from = record.valid_from or "N/A"
                valid_to = record.valid_to or "N/A"
                record.display_name = f"{sealine_name} - {record.fee_type} ({valid_from} to {valid_to})"

    @api.constrains('display_name')
    def _check_unique_display_name(self):
        """ Ensure unique display_name """
        for record in self:
            existing_quotation = self.env['pricing.quotation'].search([
                ('display_name', 'ilike', record.display_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_quotation:
                raise ValidationError(_("The Quotation '%s' already exists.") % record.display_name)

    @api.depends('booking_ids.volume_total')
    def _compute_volume_total(self):
        for record in self:
            total_teu = sum(booking.volume_total for booking in record.booking_ids if booking.volume_total)
            record.current_volume_total = total_teu

    # Calculate TEU usage
    @api.depends('sale_line_ids', 'sale_line_ids.order_id.state', 'sale_line_ids.volume_cont')
    def _compute_order_teu_usage(self):
        for record in self:
            # Calculate reserved TEU from sale order lines in 'sale' state
            reserved_teu = 0.0
            for line in record.sale_line_ids:
                if line.order_id.state == 'sale' and line.volume_cont:
                    if line.volume_cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
                        reserved_teu += line.product_uom_qty * 2  # 40ft = 2 TEU
                    elif line.volume_cont in ['20DC', '20RF', '20OT', '20HC']:
                        reserved_teu += line.product_uom_qty * 1  # 20ft = 1 TEU

            record.reserved_teu_from_orders = reserved_teu

    # Warning for TEU usage
    @api.depends('current_volume_total', 'reserved_teu_from_orders')
    def _compute_quotation_teu_warning(self):
        for record in self:
            if record.current_volume_total > 0:
                message = f"""
                    <div class="alert alert-info" role="alert">
                        <strong>Quotation TEU Summary:</strong><br/>
                        • Total Current Volume (TEU): <strong>{record.current_volume_total}</strong><br/>
                        • Reserved TEU from confirmed orders: <strong>{record.reserved_teu_from_orders}</strong>
                    </div>
                    """
                record.quotation_teu_warning_message = message
            else:
                record.quotation_teu_warning_message = ""



