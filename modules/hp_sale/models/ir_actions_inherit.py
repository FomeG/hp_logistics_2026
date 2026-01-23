from odoo import api, models

# Action XML ID that needs dynamic context
DYNAMIC_CONTEXT_ACTIONS = [
    'hp_sale.action_hp_quotations',
]


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    @api.model
    def _get_dynamic_context(self, action_xmlid):
        """
        Get dynamic context based on user role for specific actions.
        Returns empty dict if no dynamic context needed.
        """
        if action_xmlid != 'hp_sale.action_hp_quotations':
            return {}

        # Admin users: no default filter
        if self.env.user.has_group('base.group_system'):
            return {}

        user_service = self.env['hp_components.user.service']

        # DOS (sale leader): Show both department quotations and request to approval
        if user_service.is_salesman_leader():
            return {
                'search_default_my_department_quotations': 1,
                'search_default_request_to_approval': 1,
            }

        # Regular salesman: Show my quotations
        return {'search_default_my_quotation': 1}

    def read(self, fields=None, load='_classic_read'):
        """Override read to inject dynamic context for specific actions."""
        results = super().read(fields, load)

        if not fields or 'context' in fields:
            for result in results:
                # Get XML ID for this action
                action_xmlid = self._get_external_id().get(result['id'])
                if action_xmlid in DYNAMIC_CONTEXT_ACTIONS:
                    dynamic_ctx = self._get_dynamic_context(action_xmlid)
                    if dynamic_ctx:
                        # Merge dynamic context with existing context
                        existing_ctx = result.get('context', '{}')
                        if isinstance(existing_ctx, str):
                            try:
                                existing_ctx = eval(existing_ctx) if existing_ctx else {}
                            except Exception:
                                existing_ctx = {}
                        existing_ctx.update(dynamic_ctx)
                        result['context'] = str(existing_ctx)

        return results

    def _get_external_id(self):
        """Get external IDs (XML IDs) for current recordset."""
        result = {}
        for record in self:
            external_ids = self.env['ir.model.data'].sudo().search([
                ('model', '=', self._name),
                ('res_id', '=', record.id),
            ], limit=1)
            if external_ids:
                result[record.id] = f"{external_ids.module}.{external_ids.name}"
        return result
