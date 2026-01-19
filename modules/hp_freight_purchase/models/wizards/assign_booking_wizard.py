from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from collections import defaultdict
from ...models.freight_purchase_booking_inventory import FreightPurchaseBookingInventory
from ...services.freight_purchase_booking_inventory_service import FreightPurchaseBookingInventoryService
from ....hp_components.models import constants

class AssignBookingWizard(models.TransientModel):
    _name = 'assign.booking.wizard'
    _description = 'Assign Booking Wizard'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    booking_id = fields.Many2one(
        'freight.purchase.booking',
        string='Booking',
        required=True
    )
    container_type_id = fields.Many2one('container.type', string='Container', required=True)
    quantity = fields.Integer(string='Quantity', required=True)
    deadline = fields.Date(string='Deadline', required=True)

    allow_booking_ids = fields.Many2many(
        comodel_name='freight.purchase.booking',
        compute='_compute_allow_booking_ids',
        store=False,
    )
    allow_container_type_ids = fields.Many2many(
        comodel_name= 'container.type',
        compute='_compute_allow_container_type_ids',
        store=False,
    )
    inventory_summary = fields.Text(
        compute='_compute_inventory_summary',
        string="Container Inventory",
        store=False
    )

    @api.depends('sale_order_id')
    def _compute_allow_booking_ids(self):
        for rec in self:
            order = rec.sale_order_id
            if not order:
                rec.allow_booking_ids = self.env['freight.purchase.booking']
                continue
            domain = [
                ('from_location_id', '=', order.from_location_id.id),
                ('to_location_id', '=', order.to_location_id.id),
                ('etd', '>=', order.etd),
            ]
            rec.allow_booking_ids = self.env['freight.purchase.booking'].search(domain)
    
    @api.depends('booking_id')
    def _compute_allow_container_type_ids(self):
        for rec in self:
            booking = rec.booking_id
            if booking: 
                containers = {}
                for line in rec.booking_id.booking_inventory_ids:
                    qty = line.quantity or 0
                    if line.action in (
                        FreightPurchaseBookingInventory.ACTION_IN,
                        FreightPurchaseBookingInventory.ACTION_RETURN
                    ):
                        containers[line.container_type_id.id] = containers.get(line.container_type_id.id, 0) + qty
                    elif line.action == FreightPurchaseBookingInventory.ACTION_OUT:
                        containers[line.container_type_id.id] = containers.get(line.container_type_id.id, 0) - qty

                rec.allow_container_type_ids = [(6, 0, [cid for cid, total in containers.items() if total > 0])]
            else:
                rec.allow_container_type_ids = [(6, 0, [])]
    
    @api.depends('booking_id')
    def _compute_inventory_summary(self):
         for rec in self:
            booking = rec.booking_id
            if booking:
                rec.inventory_summary = booking.inventory_summary
            else:
                rec.inventory_summary = False

    def action_confirm(self):
        self.ensure_one()
        sale_order = self.sale_order_id

        container_inventory_avaliable = FreightPurchaseBookingInventoryService(self.env).count_quantity_container_available_in_booking(
            self.booking_id.id,
            self.container_type_id.id
        )

        if self.quantity > container_inventory_avaliable:
            raise ValidationError(f"No available inventory for container {self.container_type_id.name}. Please check the booking inventory.")

        booking_line = self.env['freight.purchase.booking.line'].create({
            'sale_order_id': sale_order.id,
            'booking_id': self.booking_id.id,
            'container_type_id': self.container_type_id.id,
            'quantity': self.quantity,
            'reservation_expiration_date': self.deadline,
            'unit_price': 0,
            'status': 'available',
            'quotation_line_container_type_id': self.container_type_id.id,
            'quotation_line_cost': 0,
            'quotation_line_price': 0,
        })

        sale_order.write({
            'booking_line_id': booking_line.id,
            'state': constants.SaleOrderState.READY,
            'booking_provider_id': self.env.uid,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Assign Booking Success'),
                'message': '',
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
