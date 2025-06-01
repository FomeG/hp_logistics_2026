from .base_task_service import BaseTaskService
import logging

_logger = logging.getLogger(__name__)

class CancelTaskService(BaseTaskService):
    _name = "custom_component.cancel.task.service"

    def cancel_tasks_by_sale_order(self, sale_order):
        """
        cancel all open tasks related to sale order
        """
        tasks = self._get_open_tasks_by_sale_order(sale_order)
        if tasks:
            cancelled_stage_ids = self._get_stage_ids_by_value('cancel')
            if cancelled_stage_ids:
                tasks.write({'stage_id': cancelled_stage_ids[0]})