from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError
from odoo.addons.hp_freight_purchase.services.port_route_request_service import PortRouteRequestService
import logging

_logger = logging.getLogger(__name__)

class TestPortRouteRequestService(TransactionCase):
    
    def setUp(self):
        super().setUp()
        self.service = PortRouteRequestService(self.env)
        
        # Create test data
        self.sale_order = self.env['sale.order'].create({
            'name': 'TEST-SO-001',
            'partner_id': self.env['res.partner'].create({'name': 'Test Partner'}).id,
        })
        
        self.container_type = self.env['container.type'].create({
            'name': '20DC',
            'teu': 1.0,
        })

    def test_wizard_creation(self):
        """Test that wizard can be created with valid data"""
        # Create wizard with valid data
        wizard = self.env['freight.purchase.port.route.request.wizard'].create({
            'sale_order_id': self.sale_order.id,
            'pod_name_request': 'Test POD',
            'pol_name_request': 'Test POL',
            'container_type_id': self.container_type.id,
            'etd': '2024-12-31',
        })
        
        # Verify wizard data
        self.assertTrue(wizard.sale_order_id)
        self.assertTrue(wizard.pod_name_request)
        self.assertTrue(wizard.pol_name_request)
        self.assertTrue(wizard.container_type_id)
        self.assertTrue(wizard.etd)

    def test_action_task_create_new_route_success(self):
        """Test successful task creation via listener"""
        # Create wizard
        wizard = self.env['freight.purchase.port.route.request.wizard'].create({
            'sale_order_id': self.sale_order.id,
            'pod_name_request': 'Test POD',
            'pol_name_request': 'Test POL',
            'container_type_id': self.container_type.id,
            'etd': '2024-12-31',
        })
        
        # Call the service method directly
        result = self.service.action_task_create_new_route(wizard)
        
        # Should return success notification
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')
        
        # Check that task was created
        task = self.env['project.task'].search([
            ('sale_order_id', '=', self.sale_order.id),
            ('name', 'ilike', f'POD/POL Request for {self.sale_order.name}')
        ], limit=1)
        
        self.assertTrue(task, "Task should be created")
        self.assertEqual(task.pod_name_request, 'Test POD')
        self.assertEqual(task.pol_name_request, 'Test POL')

    def test_action_task_create_new_route_validation_error(self):
        """Test validation error when required fields are missing"""
        # Create wizard with missing data
        wizard = self.env['freight.purchase.port.route.request.wizard'].create({
            'sale_order_id': self.sale_order.id,
            # Missing required fields
        })
        
        # Should raise validation error
        with self.assertRaises(UserError):
            self.service.action_task_create_new_route(wizard)

    def test_wizard_delegation(self):
        """Test that wizard properly delegates to listener"""
        # Create wizard
        wizard = self.env['freight.purchase.port.route.request.wizard'].create({
            'sale_order_id': self.sale_order.id,
            'pod_name_request': 'Test POD',
            'pol_name_request': 'Test POL',
            'container_type_id': self.container_type.id,
            'etd': '2024-12-31',
        })
        
        # Call wizard method (should delegate to listener)
        result = wizard.action_task_create_new_route()
        
        # Should return success notification
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    def test_activity_logging(self):
        """Test that activity is logged to sale order chatter"""
        # Create wizard
        wizard = self.env['freight.purchase.port.route.request.wizard'].create({
            'sale_order_id': self.sale_order.id,
            'pod_name_request': 'Test POD',
            'pol_name_request': 'Test POL',
            'container_type_id': self.container_type.id,
            'etd': '2024-12-31',
        })
        
        # Create task via service
        self.service.action_task_create_new_route(wizard)
        
        # Check that message was posted to sale order
        messages = self.sale_order.message_ids.filtered(
            lambda m: 'Port/Route Request Task Created' in m.subject
        )
        
        self.assertTrue(messages, "Activity should be logged to sale order chatter")
        
        # Check message content
        message = messages[0]
        self.assertIn('Test POD', message.body)
        self.assertIn('Test POL', message.body)
        self.assertIn('20DC', message.body) 