from odoo import models, fields

class ProductDocumentInherit(models.Model):
    _inherit = 'product.document'
    
    attached_on_sale = fields.Selection(groups=False)