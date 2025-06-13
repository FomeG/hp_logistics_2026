from odoo import fields
from odoo.tests.common import TransactionCase


class TestFreightPurchaseQuotation(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Region = self.env['freight.purchase.region']
        self.Port = self.env['freight.purchase.port']
        self.Route = self.env['freight.purchase.route']
        self.Quotation = self.env['freight.purchase.quotation']
        self.QuotationLine = self.env['freight.purchase.quotation.line']
        self.ShippingLine = self.env['res.partner'].create({
            'name': 'Test Shipping Line',
            'is_shipping_line': True
        })
        self.RegionRec = self.Region.create({
            'name': 'North America',
        })
        self.POL = self.Port.create({
            'name': 'Port A',
            'code': 'PORTA',
            'is_pod': False,
        })
        self.POD = self.Port.create({
            'name': 'Port B',
            'code': 'PORTB',
            'is_pod': True,
            'region_id': self.RegionRec.id,
        })
        self.Today = fields.Date.today()
        self.In_15_days = fields.Date.add(self.Today, days=15)

    def test_quotation_creation(self):
        route = self.Route.create({
            'pol_id': self.POL.id,
            'pod_id': self.POD.id
        })

        quotation = self.Quotation.create({
            'name': 'QTN-001',
            'shipping_line_id': self.ShippingLine.id,
            'route_id': route.id,
            'available_from': self.Today,
            'available_to': self.In_15_days
        })
        self.assertEqual(quotation.route_id.pod_id.region_id, self.RegionRec)

    def test_quotation_line_addition(self):
        route = self.Route.create({
            'pol_id': self.POL.id,
            'pod_id': self.POD.id
        })
        quotation = self.Quotation.create({
            'name': 'QTN-002',
            'shipping_line_id': self.ShippingLine.id,
            'route_id': route.id,
            'available_from': self.Today,
            'available_to': self.In_15_days
        })

        container_type = self.env['container.type'].create({
            'name': '20GP',
            'teu': 20.0
        })

        line = self.QuotationLine.create({
            'quotation_id': quotation.id,
            'container_type_id': container_type.id,
            'cost': 1500.0
        })

        self.assertEqual(line.quotation_id, quotation)
        self.assertEqual(line.container_type_id.name, '20GP')

