from odoo import models, fields, _
from odoo.exceptions import ValidationError
from ...hp_components.services.activity_service import ActivityService

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    booking_line_id = fields.Many2one(
        comodel_name= 'freight.purchase.booking.line',
        string='Booking Line id',
        index=True,
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='booking_line_id.booking_id',
        readonly=True,
        index=True,
        store=False,
    )
    booking_code = fields.Char(
        string='Booking Code',
        related='booking_id.code',
        readonly=True,
        store=False,
    )
    booking_provider_id = fields.Many2one(
        comodel_name='res.users',
        string='Booking Provider',
        store=True,
    )

    def action_assign_booking(self):
        self.ensure_one()
        return {
            'name': 'Assign Booking',
            'type': 'ir.actions.act_window',
            'res_model': 'assign.booking.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            }
        }
    
    def _notify_assign_booking(self):
        if not self.partner_id or not self.partner_id.user_id:
            return False

        service = ActivityService(
            env=self.env,
            model_name='sale.order',
            record_id=self.id,
            user_ids=self.partner_id.user_id.id
        )

        service._create_activity_by_type(
            summary=f"Your quotation has booking ref {self.booking_line_id.booking_id.name}.",
            note=''
        )

        return True