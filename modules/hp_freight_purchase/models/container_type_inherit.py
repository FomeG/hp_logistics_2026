from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.container_type_validator import ContainerTypeCreateValidator, ContainerTypeUpdateValidator

class ContainerTypeInherit(models.Model):
    _inherit = ['container.type']
    _order = 'create_date desc'

    quotation_line_ids = fields.One2many(
        comodel_name='freight.purchase.quotation.line',
        inverse_name='container_type_id',
        string='Quotation Lines'
    )

    total_quotation_lines = fields.Char(
        string="Total Quotation Lines",
        compute='_compute_total_quotation_line',
        store=False
    )

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

    @api.depends('quotation_line_ids')
    def _compute_total_quotation_line(self):
        for record in self:
            if record.quotation_line_ids:
                total = len(record.quotation_line_ids)
                record.total_quotation_lines = f"{total} Quotation Line(s)"
            else:
                record.total_quotation_lines = "0 Quotation Line(s)"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = ContainerTypeCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = ContainerTypeUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)
