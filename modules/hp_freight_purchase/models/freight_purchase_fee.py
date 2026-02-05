from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeValidator

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Freight Purchase Fee (Tariff/Contract)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        'Name',
        readonly=True,
        compute='_compute_name',
        store=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipping Line',
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        required=True,
        index=True,
        tracking=True,
    )
    from_location_id = fields.Many2one(
        string="POL",
        comodel_name='location.base',
        required=False,
        tracking=True,
    )
    to_location_id = fields.Many2one(
        string="POD",
        comodel_name='location.base',
        required=False,
        tracking=True,
    )
    date_from = fields.Date(
        string='Valid From',
        required=False,
        tracking=True,
        index=True,
    )
    date_to = fields.Date(
        string='Valid To',
        required=False,
        tracking=True,
        index=True
    )
    note = fields.Text()
    line_ids = fields.One2many(
        'freight.purchase.fee.line',
        'fee_id',
        string='Fee Lines'
    )
    notification = fields.Boolean(
        string="Send Notification",
        help="If checked, send notification to all members in Pricing department."
    )

    total_fee_lines = fields.Char(
        string="Total Fee Lines",
        compute='_compute_total_fee_lines',
        store=False
    )

    @api.depends('line_ids')
    def _compute_total_fee_lines(self):
        for record in self:
            total = len(record.line_ids)
            record.total_fee_lines = f"{total} Fee(s)" if total else "0 Fee"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        current_record = self if isinstance(self, type(self)) else self[0]
        validated, errors = FeeValidator.validate_fee(vals, self.env, mode='write', record=current_record)
        if errors:
            raise ValidationError("\n".join([f"• {e}" for e in errors]))

        res = super().write(validated if validated else vals)

        if "notification" in vals and vals['notification']:
            self._send_pricing_notification()
        return res

    @api.depends('shipping_line_id', 'from_location_id', 'to_location_id', 'date_from')
    def _compute_name(self):
        for record in self:
            parts = [record.shipping_line_id.name or '']
            
            # Add route if available
            if record.from_location_id or record.to_location_id:
                route = f"{record.from_location_id.name or '?'} → {record.to_location_id.name or '?'}"
                parts.append(route)
            
            # Add date
            if record.date_from:
                parts.append(record.date_from.strftime('%d-%m-%Y'))
            
            record.name = ' - '.join(filter(None, parts))

    @api.constrains('shipping_line_id', 'from_location_id', 'to_location_id', 'date_from', 'date_to')
    def _check_unique_fee_period(self):
        for record in self:
            domain = [
                ('shipping_line_id', '=', record.shipping_line_id.id),
                ('id', '!=', record.id)
            ]
            
            if record.from_location_id:
                domain.append(('from_location_id', '=', record.from_location_id.id))
            else:
                domain.append(('from_location_id', '=', False))
                
            if record.to_location_id:
                domain.append(('to_location_id', '=', record.to_location_id.id))
            else:
                domain.append(('to_location_id', '=', False))

            if record.date_from:
                domain.append(('date_from', '=', record.date_from))
            else:
                domain.append(('date_from', '=', False))

            # Uncomment to enforce uniqueness
            # if self.search_count(domain) > 0:
            #     raise ValidationError("Fee already exists for this shipping line, route and period.")

    def _send_pricing_notification(self):
        pricing_dept = self.env['hr.department'].sudo().search([('department_type_id.code', '=', 'pricing')], limit=1)
        if not pricing_dept:
            return

        users = pricing_dept.member_ids.mapped('user_id')
        if not users:
            return

        message_title = "Freight Fee Notification"
        message_body = f"New Fee '{self.name}' has been updated and requires your attention."

        for user in users:
            self.env['bus.bus']._sendone(
                user.partner_id,
                'simple_notification',
                {
                    'title': message_title,
                    'message': message_body,
                    'sticky': False,
                    'warning': False,
                    'type': 'success',
                }
            )
