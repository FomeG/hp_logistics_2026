from odoo import api, models

# Action XML ID that needs dynamic context
DYNAMIC_CONTEXT_ACTIONS = [
    'hp_sale.action_hp_quotations',
    'hp_sale.action_sea_freight_request',
]


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    @api.model
    def _get_dynamic_context(self, action_xmlid):
        """
        Get dynamic context based on user role for specific actions.
        Returns empty dict if no dynamic context needed.
        """
        # Admin users: no default filter for all dynamic context actions
        if self.env.user.has_group('base.group_system'):
            return {}

        # Handle quotations action
        if action_xmlid == 'hp_sale.action_hp_quotations':
            user_service = self.env['hp_components.user.service']

            # DOS (sale leader): Show both department quotations and request to approval
            if user_service.is_salesman_leader():
                return {
                    'search_default_my_department_quotations': 1,
                    'search_default_request_to_approval': 1,
                }

            # Regular salesman: Show my quotations
            return {'search_default_my_quotation': 1}

        # Handle sea freight request action (Sale module)
        if action_xmlid == 'hp_sale.action_sea_freight_request':
            return {
                'search_default_filter_open': 1,
                'search_default_my_requests': 1,
            }

        return {}

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
        if not self:
            return {}

        # Batch search: get all external_ids at once
        external_ids = self.env['ir.model.data'].sudo().search([
            ('model', '=', self._name),
            ('res_id', 'in', self.ids),
        ])

        # Build result dict
        result = {}
        for ext_id in external_ids:
            result[ext_id.res_id] = f"{ext_id.module}.{ext_id.name}"
        return result
