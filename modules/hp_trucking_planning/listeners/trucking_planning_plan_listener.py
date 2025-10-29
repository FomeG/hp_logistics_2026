# hp_trucking_planning/components/trucking_plan_listener.py
from odoo.addons.component.core import Component
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class TruckingPlanningPlanListener(Component):
    _name = 'trucking_planning.plan.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.plan']

    def on_record_create(self, record, fields=None):
        BookingModel = self.env['trucking_planning.freight.purchase.booking']
        BookingModel.sudo().create_booking_from_plan(record)