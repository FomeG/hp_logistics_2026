from odoo import models, fields


class CsTask(models.Model):
    _name = 'cs.task'
    _description = "CS Task"
    _inherits = {"project.task": "task_id"}
    _inherit = ['cs.order.detail']

    task_id = fields.Many2one(
        comodel_name="project.task",
        required=True,
        ondelete="cascade"
    )