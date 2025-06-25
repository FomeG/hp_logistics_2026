from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestFreightPurchaseCoreModels(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Region = self.env['freight.purchase.region']
        self.Port = self.env['freight.purchase.port']
        self.Route = self.env['freight.purchase.route']
        # self.ShippingLine = self.env['res.partner'].create({
        #     'name': 'Test Shipping Line',
        #     'email':'shippingline@test.com',
        #     'is_shipping_line': True
        # })
        self.Vessel = self.env['freight.purchase.vessel']

        self.RegionRec = self.Region.create({
            'name': 'North America',
            'code': 'NA11',
        })
        self.POL = self.Port.create({
            'name': 'Port A',
            'is_local': False
        })
        self.POD = self.Port.create({
            'name': 'Port B',
            'is_local': True,
            'region_id': self.RegionRec.id,
        })

    def test_vessel_code_auto_generated(self):
        vessel = self.Vessel.create({
            'name': 'Sea Titan'
        })
        self.assertTrue(vessel.code)
        self.assertNotEqual(vessel.code, '/')
        self.assertIn('S', vessel.code)  # Optional: check code logic from name

    def test_vessel_code_manual(self):
        vessel = self.Vessel.create({
            'name': 'Ocean Spirit',
            'code': 'OS-001'
        })
        self.assertEqual(vessel.code, 'OS-001')

    def test_region_create(self):
        region = self.Region.create({
            'name': 'Asia'
        })
        self.assertEqual(region.name, 'Asia')
        self.assertEqual(region.code, 'ASIA')

    def test_port_requires_region(self):
        # Test that creation without region fails
        with self.assertRaises(ValidationError):
            self.Port.create({
                'name': 'port without region',
                'code': 'PODWR',
                'is_local': True,
                'is_active': True
            })

        # Test that creation with region succeeds
        region = self.env['freight.purchase.region'].create({
            'name': 'Test Region'
        })
        port = self.Port.create({
            'name': 'Valid Port',
            'code': 'VALID',
            'region_id': region.id,
            'is_local': True
        })
        self.assertTrue(port.exists())

    def test_route_creation_and_pod_link(self):
        route = self.Route.create({
            'pol_id': self.POL.id,
            'pod_id': self.POD.id
        })
        self.assertEqual(route.region_id, self.POD.region_id)
