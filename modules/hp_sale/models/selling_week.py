from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ...hp_components.models.constants import SellingWeekState

class SellingWeek(models.Model):
    _name = 'selling.week'
    _description = 'Selling Week'
    _inherit = ['unique.code.mixin','mail.thread', 'mail.activity.mixin']
    _order = 'state_order, create_date desc'

    STATE_ORDER = {
        SellingWeekState.CURRENT: 0,
        SellingWeekState.INCOMING: 1,
        SellingWeekState.PAST: 2,
    }

    name = fields.Char(required=True, tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)
    year = fields.Char(
        string="Year",
        compute="_compute_year",
        store=True,
        index=True
    )
    state = fields.Selection([
        (SellingWeekState.CURRENT, 'Current'),
        (SellingWeekState.INCOMING, 'Incoming'),
        (SellingWeekState.PAST, 'Past')
    ],
        string="State",
        compute="_compute_state",
        store=True
    )
    product_selling_week_ids = fields.One2many(
        'product.template.selling.week',
        'selling_week_id',
        string="Product Selling Week",
        copy=True
    )

    product_selling_week_count = fields.Integer(
        string="Number of Sea Freight",
        compute="_compute_product_selling_week_count",
        store=True,
    )

    state_order = fields.Integer(string="State Order", compute="_compute_state_order", store=True)

    _sql_constraints = [
        ('check_dates', 'CHECK(start_date <= end_date)', 'End date must be after start date!')
    ]
    @api.depends("product_selling_week_ids")
    def _compute_product_selling_week_count(self):
        for rec in self:
            rec.product_selling_week_count = len(rec.product_selling_week_ids)
    @api.depends('create_date')
    def _compute_year(self):
        for rec in self:
            rec.year = rec.start_date.strftime('%Y') if rec.start_date else ''

    @api.depends('start_date', 'end_date')
    def _compute_state(self):
        today = fields.Date.today()
        for record in self:
            record.state = SellingWeekState.PAST
            if record.start_date and record.end_date:
                if today < record.start_date:
                    record.state = SellingWeekState.INCOMING
                elif today <= record.end_date:
                    record.state = SellingWeekState.CURRENT

    @api.depends('state')
    def _compute_state_order(self):
        for record in self:
            record.state_order = self.STATE_ORDER.get(record.state, 99)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = f"{self.name}-clone" if self.name else 'Unnamed-clone'
        data = self.copy_data(default)[0]
        new_record = self.create(data)
        return new_record
    
    @api.model
    def _cron_update_state(self):
        today = fields.Date.today()
        records = self.search([
            '|',
            ('state', '=', SellingWeekState.CURRENT),
            ('state', '=', SellingWeekState.INCOMING),
        ])
        for record in records:
            new_state = SellingWeekState.PAST
            if record.start_date and record.end_date:
                if today < record.start_date:
                    new_state = SellingWeekState.INCOMING
                elif today <= record.end_date:
                    new_state = SellingWeekState.CURRENT
            if record.state != new_state:
                record.state = new_state
                record.state_order = self.STATE_ORDER.get(new_state, 99)
        return True