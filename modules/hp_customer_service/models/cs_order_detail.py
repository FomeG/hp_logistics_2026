from odoo import models, fields


class CsOrderDetail(models.AbstractModel):
    _name = 'cs.order.detail'
    _description = 'CS Order Detail'

    cs_order_id = fields.Many2one(
        string='CS Order',
        comodel_name='cs.order',
        index=True,
        ondelete='cascade',
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='cs_order_id.booking_id',
        string="Booking",
    )
    cs_task_id = fields.Many2one(
        comodel_name='cs.task',
        string="Task ",
    )