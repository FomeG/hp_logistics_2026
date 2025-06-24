from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ContainerType(models.Model):
    _name = 'container.type'
    _description = 'Container Type'
    _inherit = ['unique.code.mixin','unique.normalized.name.mixin','mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    teu = fields.Float(required=True,  default=20.0, tracking=True)
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)
    quotation_line_ids = fields.One2many('freight.purchase.quotation.line', 'container_type_id', string='Quotation Lines')

    total_quotation_lines = fields.Char(string="Total Quotation Lines", compute='_compute_total_quotation_line', store=False)


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
