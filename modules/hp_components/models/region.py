from odoo import models, fields
class Region(models.Model):
    _name = 'region'
    _description = 'Region'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        required=True,
    )
    parent_id = fields.Many2one(
        comodel_name="region",
        string="Region"
    )
    child_ids = fields.One2many(
        comodel_name="region",
        inverse_name="parent_id",
        string="Sub Regions"
    )
    is_active = fields.Boolean(
        string='Is Active',
        default=True
    )
    country_ids = fields.One2many(
        comodel_name='res.country',
        inverse_name='region_id',
        string='Countries'
    )