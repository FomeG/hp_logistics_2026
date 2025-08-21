from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeValidator

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
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
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        required=True,
        index=True,
    )
    fee_type_id = fields.Many2one(
        comodel_name='freight.purchase.fee.type',
        # domain="[('is_common', '=', False)]",
        required=True,
        index=True,
        ondelete="cascade"
    )
    route_id = fields.Many2one(
        comodel_name="freight.purchase.route",
        required=False
    )
    date_from = fields.Date(
        required=False,
        tracking=True,
        index=True,
    )
    date_to = fields.Date(
        required=False,
        tracking=True,
        index=True
    )
    note = fields.Text()
    line_ids = fields.One2many(
        'freight.purchase.fee.line',
        'fee_id',
        string='Fee'
    )

    total_container_fees = fields.Char(
        string="Total Container Fees",
        compute='_compute_total_container_fees',
        store=False
    )
    container_line_ids = fields.One2many(
        'freight.purchase.fee.line',
        'fee_id',
        string='Container Fees',
        domain=[('fee_type_id.apply_on', '=', 'container')]
    )

    port_line_ids = fields.One2many(
        'freight.purchase.fee.line',
        'fee_id',
        string='Port Fees',
        domain=[('fee_type_id.apply_on', '=', 'port')]
    )
    country_id = fields.Many2one('res.country', string='Country')

    @api.depends('line_ids')
    def _compute_total_container_fees(self):
        for record in self:
            if record.line_ids:
                total = len(record.line_ids)
                record.total_container_fees = f"{total} Fee(s)"
            else:
                record.total_container_fees = "0 Fee"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = FeeValidator.validate_fee(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))

        fees = super().create(vals_list)
        for fee in fees:
            fee._create_fee_lines_from_country()
        return fees


    def write(self, vals):
        current_record = self if isinstance(self, type(self)) else self[0]
        validated, errors = FeeValidator.validate_fee(vals, self.env, mode='write', record=current_record)
        if errors:
            raise ValidationError("\n".join([f"• {e}" for e in errors]))

        res = super().write(validated if validated else vals)

        if "country_id" in vals:
            for fee in self:
                fee._create_fee_lines_from_country()
        return res


    @api.depends('shipping_line_id', 'fee_type_id','date_from')
    def _compute_name(self):
        for record in self:
            date_str = record.date_from.strftime('%d-%m-%Y') if record.date_from else ''
            record.name = f"{record.shipping_line_id.name or ''} - {record.fee_type_id.name or ''} - {date_str}".strip(
                ' -')

    @api.onchange('fee_type_id')
    def _onchange_fee_type(self):
        if self.fee_type_id.apply_on == 'container':
            self.port_line_ids = [(5, 0, 0)]  # xóa port lines
        elif self.fee_type_id.apply_on == 'port':
            self.container_line_ids = [(5, 0, 0)]  # xóa container lines

    @api.constrains('fee_type_id', 'shipping_line_id', 'date_from')
    def _check_unique_fee_period(self):
        for record in self:
            domain = [
                ('fee_type_id', '=', record.fee_type_id.id),
                ('shipping_line_id', '=', record.shipping_line_id.id),
                ('id', '!=', record.id)
            ]

            if record.date_from:
                domain.append(('date_from', '=', record.date_from))
            else:
                domain.append(('date_from', '=', False))

            # if self.search_count(domain) > 0:
            #     raise ValidationError(f"Fee already exists for this shipping line and period.")

    show_container_lines = fields.Char(compute='_compute_show_lines', store=False)
    show_port_lines = fields.Char(compute='_compute_show_lines', store=False)

    @api.onchange('fee_type_id')
    def _compute_show_lines(self):
        for rec in self:
            rec.show_container_lines = 'container' if rec.fee_type_id.apply_on == 'container' else ''
            rec.show_port_lines = 'port' if rec.fee_type_id.apply_on == 'port' else ''
    def _create_fee_lines_from_country(self):
        if not self.country_id or not self.fee_type_id:
            return

        ports = self.env["freight.purchase.port"].search([
            ("country_id", "=", self.country_id.id)
        ])
        FeeLine = self.env["freight.purchase.fee.line"]

        for port in ports:
            exists = FeeLine.search([
                ("fee_id", "=", self.id),
                ("port_id", "=", port.id),
            ], limit=1)
            if exists:
                continue

            FeeLine.create({
                "fee_id": self.id,
                "port_id": port.id,
                "country_id": self.country_id.id,
                "container_type_id": False if self.fee_type_id.apply_on != "container" else None,
            })
    @api.depends('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.fee_type_id and self.fee_type_id.apply_on == 'port':
            ports = self.env["freight.purchase.port"].search([
                ("country_id", "=", self.country_id.id)
            ])
            self.port_line_ids = [(5, 0, 0)]  # clear trước
            self.port_line_ids = [(0, 0, {
                "port_id": port.id,
                "country_id": self.country_id.id,
            }) for port in ports]
