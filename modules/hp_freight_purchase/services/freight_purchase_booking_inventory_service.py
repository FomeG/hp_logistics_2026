class FreightPurchaseBookingInventoryService:
    _name = "Freight Purchase Booking Inventory Service"
    def __init__(self, env):
        self.env = env

    def create_inventory_by_booking_line(self, booking_line, action) -> None:
        inventory_vals = {
            'booking_id': booking_line.booking_id.id,
            'booking_line_id': booking_line.id,
            'container_type_id': booking_line.container_type_id.id,
            'quantity': booking_line.quantity,
            'action': action,
        }
        self.env['freight.purchase.booking.inventory'].sudo().create(inventory_vals)
        return
    
    def count_quantity_container_available_in_booking(self, booking_id, container_type_id):
        domain = [
            ('booking_id', '=', booking_id),
            ('container_type_id', '=', container_type_id),
        ]

        records = self.env['freight.purchase.booking.inventory'].sudo().search(domain)

        in_qty = sum(r.quantity for r in records if r.action in ('in', 'return'))
        out_qty = sum(r.quantity for r in records if r.action == 'out')

        return in_qty- out_qty
