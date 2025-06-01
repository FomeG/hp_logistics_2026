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
        self._handle_project_task_created(record)

    def on_record_write(self, record, fields=None):
        self._handle_project_task_updated(record)

    def _handle_project_task_created(self, task):
        if task.user_ids:
            service = ActivityService(
                env=self.env,
                model_name='project.task',
                record_id=task.id,
                user_ids=task.user_ids.ids)
            service.create_price_request(
                summary='New Task Assigned',
                note=f'<p>You have been assigned a new task: <b>{task.name}</b></p>'
            )
        else:
            _logger.info('No tasks assigned')

    def _handle_project_task_updated(self, task):
        service = TaskService(self.env)
        service.update_sale_order_line_price_by_task(task)