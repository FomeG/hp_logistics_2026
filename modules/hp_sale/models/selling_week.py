from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SellingWeek(models.Model):
    _name = 'selling.week'
    _description = 'Selling Week'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin','mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)

    _sql_constraints = [
        ('check_dates', 'CHECK(start_date <= end_date)', 'End date must be after start date!')
    ]
