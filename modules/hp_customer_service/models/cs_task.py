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
    
    # project_id = fields.Many2one(
    #     'project.project',
    #     related='cs_order_id.project_id',
    #     store=True,
    #     precompute=True,
    # )

    # stage_id = fields.Many2one(
    #     'project.task.type',
    #     string='Stage',
    #     domain="[('project_ids','=',project_id)]",
    #     related='task_id.stage_id',
    #     store=True,
    #     readonly=False,
    # )

    @api.model_create_multi
    def create(self, vals_list):
        # Collect sale_order data for post-create update
        sale_order_map = {}

        for idx, vals in enumerate(vals_list):
            cs_order_id = vals.get('cs_order_id')
            if not cs_order_id:
                continue

            cs_order = self.env['cs.order'].browse(cs_order_id)
            if not cs_order.exists():
                continue

            if cs_order.project_id and 'project_id' not in vals:
                vals['project_id'] = cs_order.project_id.id

            if cs_order.sale_order_id:
                sale_order_map[idx] = cs_order.sale_order_id.id

        records = super().create(vals_list)

        for idx, record in enumerate(records):
            sale_order_id = sale_order_map.get(idx)
            if sale_order_id and record.task_id:
                record.task_id.sale_order_id = sale_order_id

        return records
