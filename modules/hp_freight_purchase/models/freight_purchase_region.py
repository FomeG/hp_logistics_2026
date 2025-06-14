from odoo import models, fields

class FreightPurchaseRegion(models.Model):
    _name = 'freight.purchase.region'
    _description = 'Region'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)
    ports = fields.One2many('freight.purchase.port','region_id',string='Ports', tracking=True)
    employee_ids = fields.Many2many('hr.employee', string='Pricing Members', tracking=True)