# -*- coding: utf-8 -*-

from odoo import api, models

# Action XML ID that needs dynamic context
DYNAMIC_CONTEXT_ACTIONS = [
    'hp_freight_purchase.action_price_request_freight_purchase',
]


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    @api.model
    def _get_dynamic_context_freight_purchase(self, action_xmlid):
        """
        Get dynamic context based on user role for freight purchase actions.
        Returns empty dict if no dynamic context needed.
        """
        # Admin users: no default filter
        if self.env.user.has_group('base.group_system'):
            return {}

        # Handle price request action (Freight Purchase module)
        if action_xmlid == 'hp_freight_purchase.action_price_request_freight_purchase':
            return {
                'search_default_filter_open': 1,
                'search_default_assigned_to_me': 1,
            }

        return {}

    def read(self, fields=None, load='_classic_read'):
        """Override read to inject dynamic context for freight purchase actions."""
        results = super().read(fields, load)

        if not fields or 'context' in fields:
            for result in results:
                # Get XML ID for this action
                action_xmlid = self._get_external_id_freight_purchase().get(result['id'])
                if action_xmlid in DYNAMIC_CONTEXT_ACTIONS:
                    dynamic_ctx = self._get_dynamic_context_freight_purchase(action_xmlid)
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

    def _get_external_id_freight_purchase(self):
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
