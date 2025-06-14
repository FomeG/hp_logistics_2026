from odoo.tests.common import TransactionCase
from odoo import fields

class TestFreightPurchaseBooking(TransactionCase):

    def setUp(self):
        super().setUp()
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']
        self.ContainerType = self.env['container.type']
        self.Vessel = self.env['freight.purchase.vessel']
        self.Region = self.env['freight.purchase.region']
        self.Port = self.env['freight.purchase.port']
        self.Route = self.env['freight.purchase.route']
        self.Quotation = self.env['freight.purchase.quotation']
        self.QuotationLine = self.env['freight.purchase.quotation.line']
        self.Booking = self.env['freight.purchase.booking']
        self.BookingLine = self.env['freight.purchase.booking.line']


        # Required related data
        self.container_type = self.ContainerType.create({
            'name': '20GP',
            'teu': 20.0,
        })
        shippingLine = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'is_shipping_line': True
        })
        self.vesselRec = self.Vessel.create({
            'name': 'Sea Titan'
        })
        regionRec = self.Region.create({
            'name': 'North America',
            'code': 'NA',
        })
        pol = self.Port.create({
            'name': 'Port A',
            'code': 'PORTA',
            'is_pod': False,
        })
        pod = self.Port.create({
            'name': 'Port B',
            'code': 'PORTB',
            'is_pod': True,
            'region_id': regionRec.id,
        })
        today = fields.Date.today()
        in_15_days = fields.Date.add(today, days=15)
        route = self.Route.create({
            'pol_id': pol.id,
            'pod_id': pod.id
        })
        quotation = self.Quotation.create({
            'name': 'QTN-001',
            'shipping_line_id': shippingLine.id,
            'route_id': route.id,
            'available_from': today,
            'available_to': in_15_days
        })

        container_type = self.env['container.type'].create({
            'name': '20GP',
            'teu': 20.0
        })

        self.QuotationLineRec = self.QuotationLine.create({
            'quotation_id': quotation.id,
            'container_type_id': container_type.id,
            'cost': 1500.0
        })
        self.product = self.env['product.product'].create({
            'name': 'Freight Product',
        })
        self.sale_order = self.SaleOrder.create({
            'partner_id': self.env.ref('base.res_partner_1').id,
        })

        self.booking = self.Booking.create({
                'name': 'Test Booking',
                'quotation_id': self.QuotationLineRec.quotation_id.id,
                'vessel_id': self.vesselRec.id,
                'etd': fields.Date.today(),
            })
        self.bookingLine = self.BookingLine.create({
            'booking_id': self.booking.id,
            'quotation_line_id': self.QuotationLineRec.id,
            'quantity': 3,
        })
    def test_create_booking_line(self):

        self.assertTrue(self.bookingLine.container_type_id)
        self.assertEqual(self.bookingLine.status, 'available')

    def test_assign_unassign_sale_order_line(self):
        sale_order_line = self.SaleOrderLine.create({
            'order_id': self.sale_order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
            'booking_line_id': self.bookingLine.id,
        })
        self.assertEqual(self.bookingLine.customer_id, self.sale_order.partner_id)
        sale_order_line.write({'booking_line_id': False})
        self.assertFalse(self.bookingLine.customer_id)

    # def test_unassign_and_create_history(self):
    #     booking_line = self.BookingLine.create({
    #         'quotation_line_id': self.env.ref('your_module.sample_quotation_line').id,
    #         'quantity': 1,
    #     })
    #
    #     sale_line = self.SaleOrderLine.create({
    #         'order_id': self.sale_order.id,
    #         'product_id': self.product.id,
    #         'product_uom_qty': 1,
    #         'booking_line_id': booking_line.id,
    #     })
    #
    #     # Force unlinking
    #     booking_line.write({
    #         'sale_order_line_ids': [(3, sale_line.id)]
    #     })
    #
    #     history = self.env['freight.booking.line.history'].search([
    #         ('booking_line_id', '=', booking_line.id),
    #         ('sale_order_line_id', '=', sale_line.id),
    #         ('event_type', '=', 'unassign')
    #     ])
    #     self.assertEqual(len(history), 1)
