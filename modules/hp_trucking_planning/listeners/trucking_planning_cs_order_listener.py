from odoo.addons.component.core import Component
from odoo.addons.hp_components.models import constants


class TruckingPlanningCsOrderListener(Component):
    _name = 'trucking.plan.cs.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['cs.order']

    def on_record_create(self, record, fields=None):
        self.env['trucking_planning.plan'].get_or_create_from_cs_order(record)

    def on_record_write(self, record, fields=None):
        """
        Kích hoạt khi cs.order được cập nhật trạng thái
        """
        if 'state' not in fields:
            return

        old_state = record._origin.state
        new_state = record.state

        # xử lý khi chuyển từ draft -> in_progress
        if old_state == constants.CsOrderState.DRAFT and new_state == constants.CsOrderState.IN_PROGRESS:
            self._create_trucking_planning_from_cs_order(record)

    def _create_trucking_planning_from_cs_order(self, cs_order):
        """
        Tạo Plan, Plan Line, và Trip (draft) từ cs.order
        """
        plan = self.env['trucking_planning.plan'].get_or_create_from_cs_order(cs_order)

        for job in cs_order.job_ids:
            plan_line = self.env['trucking_planning.plan.line'].get_or_create_from_cs_job(job, plan)

            # Tạo draft trip cho mỗi container (nếu cần)
            if job.container_ids:
                for container in job.container_ids:
                    self.env['trucking_planning.trip'].get_or_create_draft_from_container(container, plan_line)
            else:
                # Nếu không có container cụ thể, tạo 1 draft trip mặc định
                self.env['trucking_planning.trip'].get_or_create_draft_from_job(job, plan_line)