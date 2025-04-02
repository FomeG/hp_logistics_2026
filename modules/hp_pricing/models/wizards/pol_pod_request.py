from odoo import fields, models, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)
class PodPolRequestWizard(models.TransientModel):
    _name = 'pod.pol.request.wizard'
    _description = 'POD/POL Request Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    etd = fields.Date(string="ETD", required=True, default=fields.Date.today())
    pod_name_request = fields.Char('POD name request', required=True)
    pol_name_request = fields.Char('POL name request', required=True)

    def action_create_task(self):
        self.ensure_one()
        project = self.env['project.project'].search([('type', '=', 'request_product')], limit=1)

        if not project:
            raise UserError(_("No project found with type 'request_product'. Please create it first."))

        # Create task with the collected information
        task = self.env['project.task'].create({
            'name': f'POD/POL Request for {self.sale_order_id.name}',
            'project_id': project.id,
            'sale_order_id': self.sale_order_id.id,
            'etd': self.etd,
            'pod_name_request': self.pod_name_request,
            'pol_name_request': self.pol_name_request,
        })

        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Task Created'),
                'message': _('POD/POL Request task created successfully!'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }