

class BaseTaskService():
    _name = 'custom_component.base.task.service'

    def __init__(self, env):
        self.env = env
        self._stage_cache_by_value = {}
        self._stage_cache_by_xml = {}

    def _get_stage_ids_by_value(self, value: str):
        """Memoized search by 'ilike' value"""
        if value not in self._stage_cache_by_value:
            self._stage_cache_by_value[value] = self.env['project.task.type'].search([
                ('name', 'ilike', value)
            ]).ids
        return self._stage_cache_by_value[value]

    def _get_open_tasks_by_sale_order(self, sale_order):
        done_stage_ids = self._get_stage_ids_by_value('done')
        cancelled_stage_ids = self._get_stage_ids_by_value('cancel')

        return self.env['project.task'].search([
            ('sale_order_id', '=', sale_order.id),
            ('stage_id', 'not in', done_stage_ids + cancelled_stage_ids)
        ])

    def _sale_order_line_has_open_task(self, sale_order_line) -> bool:
        done_stage_ids = self._get_stage_ids_by_value('done')
        cancelled_stage_ids = self._get_stage_ids_by_value('cancel')
        return self.env['project.task'].search_count([
            ('sale_line_id', '=', sale_order_line.id),
            ('stage_id', 'not in', done_stage_ids + cancelled_stage_ids)
        ]) > 0