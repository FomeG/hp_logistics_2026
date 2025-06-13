from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

#python3 odoo-bin -c odoo.conf -d logistics -i hp_freight_purchase --test-enable --stop-after-init
class TestContainerType(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ContainerType = self.env['container.type']

        # Test data
        self.container_data = {
            'name': 'Standard Dry Container',
            'teu': 1.0,
            'is_active': True
        }
        # Clear existing container.type records
        self.ContainerType.search([]).unlink()

    def test_01_auto_code_generation(self):
        container = self.ContainerType.create(self.container_data)
        self.assertEqual(container.code, 'SDC',f"Should generate code from first letters of each word (got {container.code})")

    def test_02_manual_code_assignment(self):
        custom_code = "STD20"
        container = self.ContainerType.create({
            **self.container_data,
            'code': custom_code
        })
        self.assertEqual(container.code, custom_code,"Should preserve manually entered code")

    def test_03_code_uniqueness(self):
        code = "TEST123"
        self.ContainerType.create({**self.container_data, 'code': code})
        with self.assertRaises(ValidationError):
            self.ContainerType.create({**self.container_data, 'code': code})

    def test_04_teu_positive_constraint(self):
        with self.assertRaises(ValidationError):
            self.ContainerType.create({
                **self.container_data,
                'teu': -1.5
            })

    def test_05_name_required(self):
        with self.assertRaises(ValidationError):
            self.ContainerType.create({
                'teu': 1.0,
                'code': 'NO_NAME'
            })

    # # ---- TEST BUSINESS LOGIC ----
    def test_06_code_generation_rules(self):
        test_cases = [
            ('High Cube Container', 'HCC'),
            ('Reefer 40ft', 'R4'),
            ('Open Top', 'OT'),
            ('Tank Container', 'TC'),
        ]
        for name, expected_code in test_cases:
            container = self.ContainerType.create({
                'name': name,
                'teu': 1.0
            })
            self.assertEqual(container.code, expected_code, f"Failed for '{name}': expected {expected_code}, got {container.code}")

    def test_07_active_records_filter(self):

        active_container = self.ContainerType.create(self.container_data)

        inactive_container = self.ContainerType.create({
            **self.container_data,
            'name': 'Inactive Container',
            'is_active': False
        })

        active_records = self.ContainerType.search([('is_active', '=', True)])
        self.assertIn(active_container.id, active_records.ids)
        self.assertNotIn(inactive_container.id, active_records.ids)

    # # ---- TEST EDGE CASES ----
    def test_08_empty_name_code_generation(self):
        """Test code generation with empty name"""
        with self.assertRaises(ValidationError):
            self.ContainerType.create({
                'name': '',
                'teu': 1.0
            })

    def test_09_special_characters_in_name(self):
        """Test name with special characters generates proper code"""
        test_cases = [
            ('Flat-Rảck Container (40ft)', 'FRC'),
            ('Tank-Containé & (Chemical)', 'TCC'),
            ('Open-Top|20ft', 'OT'),
            ('High Cube "Special"', 'HCS'),
            ('Refeer (40ft) w/Generator', 'R4W')
        ]

        for name, expected_code in test_cases:
            with self.subTest(name=name, expected=expected_code):
                container = self.ContainerType.create({
                    'name': name,
                    'teu': 2.0
                })
                self.assertEqual(
                    container.code,
                    expected_code,
                    f"Failed for '{name}': expected {expected_code}, got {container.code}"
                )

    def test_10_batch_creation(self):
        containers = self.ContainerType.create([
            {'name': 'Type A', 'teu': 1.0},
            {'name': 'Type B', 'teu': 1.5, 'code': 'CUSTOM'},
            {'name': 'Type C', 'teu': 2.0}
        ])

        self.assertEqual(len(containers), 3)
        self.assertEqual(containers[0].code, 'TA')
        self.assertEqual(containers[1].code, 'CUSTOM')
        self.assertEqual(containers[2].code, 'TC')

    def test_11_mass_creation_performance(self):
        containers = self.ContainerType.create([
            {'name': f'Container {i}', 'teu': 1.0}
            for i in range(1000)
        ])
        self.assertEqual(len(containers), 1000)