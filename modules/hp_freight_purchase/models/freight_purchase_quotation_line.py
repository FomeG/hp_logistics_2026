from odoo import models, fields, api

class FreightPurchaseQuotationLine(models.Model):
    _name = 'freight.purchase.quotation.line'
    _description = 'Purchase Quotation Line'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    quotation_id = fields.Many2one('freight.purchase.quotation', required=True, ondelete='cascade')
    container_type_id = fields.Many2one('container.type', required=True)
    cost = fields.Float(string="Booking price",required=True)
    price = fields.Float(string="Internal price set by sale director",default=lambda self: self.cost if self.cost else 0.0)

    name = fields.Char(string="Name", compute='_compute_name', store=False)

    @api.depends('quotation_id', 'container_type_id')
    def _compute_name(self):
        for record in self:
            record.name = False
            if record.quotation_id and record.container_type_id:
                record.name = f"Quotation: {record.quotation_id.name} for container type: {record.container_type_id.name}"
                