from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.fee_validator import FeeCreateValidator, FeeUpdateValidator

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']
    _order = 'create_date desc'

    name = fields.Char(required=True, tracking=True)
    amount = fields.Float(required=False, tracking=True)
    quotations = fields.Many2many('freight.purchase.quotation', string='Quotations')

    total_quotation = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('quotations')
    def _compute_total_quotation(self):
        for record in self:
            if record.quotations:
                total = len(record.quotations)
                record.total_quotation = f"{total} Quotation(s)"
            else:
                record.total_quotation = "0 Quotation(s)"
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = FeeCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)
    
    def write(self, vals):
        for record in self:
            validated, errors = FeeUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)