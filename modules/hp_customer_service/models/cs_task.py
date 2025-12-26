from odoo import models, fields, api


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

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to set sale_order_id on the project.task record.
        This allows salesman to read CS tasks of their sale orders via ir.rule.
        """
        for vals in vals_list:
            if 'cs_order_id' in vals and 'sale_order_id' not in vals:
                cs_order = self.env['cs.order'].browse(vals['cs_order_id'])
                if cs_order.sale_order_id:
                    vals['sale_order_id'] = cs_order.sale_order_id.id
        return super().create(vals_list)