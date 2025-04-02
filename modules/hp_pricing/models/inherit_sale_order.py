from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_create_pricing_sealine(self):
        """Opens a form to create a new project task for pricing sealine"""
        return {
            'name': 'Create Pricing Sealine',
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'new',  # Opens in a popup
            'context': {
                'default_name': 'New Pricing Sealine',
                'default_project_id': self.env['project.project'].search([('type', '=', 'request_product')],
                                                                         limit=1).id,
                'default_sale_order_id': self.id,
            },
        }