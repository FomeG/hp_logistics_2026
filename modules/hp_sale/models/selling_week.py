from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ...hp_components.models.constants import SellingWeekState

class SellingWeek(models.Model):
    _name = 'selling.week'
    _description = 'Selling Week'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin','mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

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
        (SellingWeekState.PASS, 'Past')
    ],
        string="State",
        default=SellingWeekState.CURRENT,
        required=True
    )

    _sql_constraints = [
        ('check_dates', 'CHECK(start_date <= end_date)', 'End date must be after start date!')
    ]
    
    @api.depends('create_date')
    def _compute_year(self):
        for rec in self:
            rec.year = rec.start_date.strftime('%Y') if rec.start_date else ''