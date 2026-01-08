from odoo import fields, models, api, _
from odoo.addons.hp_freight_purchase.services.freight_purchase_port_route_request_service import PortRouteRequestService

import logging
_logger = logging.getLogger(__name__)

class PortRouteRequestWizard(models.TransientModel):
    _name = 'freight.purchase.port.route.request.wizard'
    _description = 'Port/Route Request Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    # sale_order_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    etd = fields.Date(string="ETD", required=True, default=fields.Date.today())
    pod_name_request = fields.Char('POD (Port of Discharge) name request', required=True)
    pol_name_request = fields.Char('POL (Port of Loading) name request', required=True)
    container_type_id = fields.Many2one(
        'container.type',
        string="Container Type (For this quotation)",
        required=True,
        default=lambda self: self.env['container.type'].search([('name', '=', '20DC')], limit=1),
        domain=[('is_active', '=', True)],
    )
    notes = fields.Text('Additional Notes')

    def action_task_create_new_route(self):
        """Create a task for new route/port request"""
        self.ensure_one()

        service = PortRouteRequestService(self.env)
        return service.action_task_create_new_route(self)