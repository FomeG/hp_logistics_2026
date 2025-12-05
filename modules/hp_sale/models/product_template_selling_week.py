from odoo import models, fields, api
from odoo.addons.hp_components.models.constants import LocationType

class ProductTemplateSellingWeek(models.Model):
    _name = 'product.template.selling.week'
    _description = 'Product Template Selling Week'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    goods_info = fields.Char(
        string="Goods Info",
        required=True,
        tracking=True
    )
    selling_week_id = fields.Many2one(
        'selling.week',
        string="Selling Week",
        tracking=True
    )
    from_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POL",
        tracking=True,
        index=True,
        domain="[('is_local', '=', True),('type', '=','port')]"
    )
    to_location_id = fields.Many2one(
        comodel_name='location.base',
        string="POD",
        tracking=True,
        index=True,
        domain="[('id', 'in', available_location_ids)]"
    )
    team_id = fields.Many2one(
        'hr.team',
        string="Team",
        tracking=True
    )
    region_id = fields.Many2one(
        comodel_name='region',
        string="Region",
        related='team_id.region_id'
    )
    line_ids = fields.One2many(
        'product.template.selling.week.line',
        'product_template_selling_week_id',
        tracking=True,
        copy=True
    )
    note = fields.Char()

    name = fields.Text(string="Name", compute="_compute_name", store=True)
    available_location_ids = fields.Many2many(
        comodel_name='location.base',
        compute='_compute_available_location_ids',
        store=False
    )
    week_info = fields.Char(
        string="Week",
        compute='_compute_week_info',
        store=False,
    )

    @api.depends('goods_info', 'from_location_id', 'to_location_id', 'line_ids')
    def _compute_name(self):
        for record in self:
            goods_part = record.goods_info or ''
            location_part = f"{record.from_location_id.name} - {record.to_location_id.name}"

            line_parts = []
            for line in record.line_ids:
                container = line.container_type_id.name or ''
                price = str(line.price or '')
                fees =  line.product_tag_ids.mapped('name')
                fee_string = ', '.join(fees) if fees else ''
                ship = line.shipping_line_id.name or ''
                line_parts.append(f"{container}/{price} {fee_string} ({ship})")

            lines_text = ', '.join(line_parts) if line_parts else ''

            if goods_part or location_part or lines_text:
                record.name = f"{goods_part}\n{location_part}: {lines_text}"
            else:
                record.name = ''

    def _compute_week_info(self):
        for record in self:
            record.week_info = f"{record.selling_week_id.name} ({record.selling_week_id.start_date} - {record.selling_week_id.end_date})"

    @api.depends('team_id')
    def _compute_available_location_ids(self):
        for record in self:
            if record.team_id:
                record.available_location_ids = record.team_id.location_ids
            else:
                record.available_location_ids = []