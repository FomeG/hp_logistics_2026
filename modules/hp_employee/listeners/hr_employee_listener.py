from odoo.addons.component.core import Component

class HrEmployeeListener(Component):
    _name = "hr.employee.listener"
    _description = "Hr Employee listener"
    _inherit = 'base.event.listener'
    _apply_on = ['hr.employee']

    def on_record_create(self, record, fields=None):
        record.with_delay().auto_create_user()
        return