from odoo import models, fields

class SellingWeekInherit(models.Model):
    _inherit = 'selling.week'

    freight_purchase_quotation_id = fields.Many2one(
        'freight.purchase.quotation',
        string="Freight Purchase Quotation",
        copy=False
    )