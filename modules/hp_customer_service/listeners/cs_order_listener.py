from odoo.addons.component.core import Component


class CsOrderListener(Component):
    _name = 'cs.order.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['cs.order']

    def on_record_create(self, record, fields=None):
        # khi cs order dc tạo -> đảm bảo projcet liên quan có stage, nếu chưa có → gắn default stages
        self._ensure_project_has_stages(record)






    def _ensure_project_has_stages(self, record):
        """Link default stages to the project if none exist"""
        if not record.project_id:
            return

        # Check if project already has stages
        if record.project_id.type_ids:
            return

        # Get default project stages (not personal stages)
        default_stages = self.env['project.task.type'].search([
            ('user_id', '=', False),  # Only project stages, not personal
            ('active', '=', True),
        ], order='sequence', limit=4)

        if default_stages:
            record.project_id.write({
                'type_ids': [(6, 0, default_stages.ids)]
            })
