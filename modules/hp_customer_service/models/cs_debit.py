from odoo import models


class CsDebit(models.Model):
    _name = 'cs.debit'
    _inherit = ['cs.order.detail']
    _description = 'Customer Service Debit'