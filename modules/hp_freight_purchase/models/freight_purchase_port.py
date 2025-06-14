from odoo import models, fields,api

from odoo.exceptions import ValidationError

class FreightPurchasePort(models.Model):
    _name = 'freight.purchase.port'
    _description = 'Port'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    is_pod = fields.Boolean(string='Is POD',default=True, tracking=True)
    region_id = fields.Many2one('freight.purchase.region', string='Region', tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)

    @api.constrains('is_pod', 'region_id')
    def _check_region_required(self):
        for record in self:
            if record.is_pod:
                if not record.region_id:
                    raise ValidationError("Region is required for POD (Port of Discharge).")
                    # Check if the region exists in the database
                if not record.region_id.exists():
                    raise ValidationError("Selected region does not exist in the system.")
