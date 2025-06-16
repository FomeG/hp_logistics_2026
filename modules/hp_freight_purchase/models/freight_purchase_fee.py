from odoo import models, fields, api

class FreightPurchaseFee(models.Model):
    _name = 'freight.purchase.fee'
    _description = 'Additional Fee from Shipping Line'
    _inherit = ['unique.code.mixin', 'mail.thread', 'mail.activity.mixin']

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