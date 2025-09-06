from odoo.addons.component.core import Component
from odoo import fields

class PlanLineListener(Component):
    _name = 'trucking_planning.plan_line_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.plan.line']

    def on_record_create(self, record, fields=None):
        pass

    def on_record_write(self, record, fields=None):
        pass
