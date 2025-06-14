from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ContainerType(models.Model):
    _name = 'container.type'
    _description = 'Container Type'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    teu = fields.Float(required=True,  default=20.0, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if not record.name or not record.name.strip():
                raise ValidationError(f"Name is required and cannot be empty!")

    @api.constrains('teu')
    def _check_teu_positive(self):
        """Ensure TEU is always positive"""
        for record in self:
            if record.teu <= 0:
                raise ValidationError(f"TEU must be a positive number")
