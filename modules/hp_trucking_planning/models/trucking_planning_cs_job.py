from .plan_line import PlanLine
from odoo import models, fields, api
import logging


_logger = logging.getLogger(__name__)

class TruckingPlanningCsJob(models.Model):
    _name = 'trucking_planning.cs.job'
    _inherits = {'cs.job':'job_id'}

    job_id = fields.Many2one(
        comodel_name='cs.job',
        string='Cs Job',
        required=True,
        ondelete='cascade',
        index=True,
    )
    @api.model
    def create_job_from_plan_line(self, record: PlanLine):
        try:
            job_vals = {
                'booking_id': record.plan_id.booking_id.id,
                'job_number': record.code,
                'service_type': 'door-cy',
                'department_code': 'JP01',
            }
            job = super(TruckingPlanningCsJob,self).create(job_vals)
            _logger.info(f"[PlanLine→Job] Created CS Job {job.job_number} from Plan Line {record.code}")
            record.write({'job_id': job.job_id})

        except Exception as e:
            _logger.error(f"Failed to create job from plan_line {e}")