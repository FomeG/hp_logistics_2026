from odoo.addons.component.core import Component


class TruckingPlanningCsOrderListener(Component):
    _name = 'trucking.plan.cs.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['cs.order']

    def on_record_create(self, record, fields=None):
        self.env['trucking_planning.plan'].get_or_create_from_cs_order(record)