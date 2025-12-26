from odoo import models, fields


class CsTask(models.Model):
    _name = 'cs.task'
    _description = "CS Task"
    _inherits = {"project.task": "task_id"}
    _inherit = ['cs.order.detail', 'mail.thread', 'mail.activity.mixin']

    task_id = fields.Many2one(
        comodel_name="project.task",
        required=True,
        ondelete="cascade"
    )

    project_id = fields.Many2one(
        'project.project',
        related='cs_order_id.project_id',
        store=True,
        precompute=True,
    )
    
    stage_id = fields.Many2one(
        'project.task.type',
        string='Stage',
        domain="[('project_ids','=',project_id)]",
        related='task_id.stage_id',
        store=True,
        readonly=False,
    )