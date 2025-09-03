from odoo import models, fields, api

class FreightPurchaseShippingLineEmail(models.Model):
    _name = 'hp.freight.purchase.shipping.line.email'
    _description = 'Shipping Line Emails'
    _order = 'create_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Shipping Line',
        required=True,
        ondelete='cascade'
    )
    email = fields.Char(string='Email', required=True)
    note = fields.Char(string='Description')
    is_primary = fields.Boolean(string='Primary')
