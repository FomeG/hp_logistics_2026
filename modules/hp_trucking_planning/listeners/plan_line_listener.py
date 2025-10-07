from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)

class PlanLineListener(Component):
    _name = 'trucking.plan.line.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['trucking_planning.plan.line']

    def on_record_create(self, record, fields=None):
        """
        Khi plan line được tạo -> tự động tạo CS Job và gắn booking từ plan
        """
        try:
            job_model = self.env['cs.job']
            plan = record.plan_id
            booking = plan.booking_id  # lấy booking đã tạo từ plan

            job_vals = {
                'booking_id': booking.id if booking else False,
                'job_number': self.env['ir.sequence'].next_by_code('cs.job.sequence'),
                'service_type': 'door-cy',
                'department_code': 'JP01',  # tuỳ chỉnh theo logic bạn muốn

                # có thể thêm các field khác từ plan_line nếu cần
            }

            job = job_model.create(job_vals)
            _logger.info(f"[PlanLine→Job] Created CS Job {job.job_number} from Plan Line {record.code}")

            record.message_post(body=f"CS Job <b>{job.job_number}</b> was auto-created from this plan line.")
        except Exception as e:
            _logger.error(f"Error auto-creating CS Job from plan line {record.code}: {str(e)}")
