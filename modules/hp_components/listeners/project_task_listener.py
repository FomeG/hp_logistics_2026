from odoo.addons.component.core import Component
from ..services.activity_service import ActivityService
from ..services.sale_order_service import SaleOrderService

import logging

from ..services.task_service import TaskService

_logger = logging.getLogger(__name__)

class ProjectTaskListener(Component):
    _name = 'custom_component.project_task_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['project.task']

    def on_record_create(self, record, fields=None):
        record.with_delay()._handle_project_task_created()

    def on_record_write(self, record, fields=None):
        record.with_delay()._handle_project_task_updated()