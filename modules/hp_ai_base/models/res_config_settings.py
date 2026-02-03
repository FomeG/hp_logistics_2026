from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Default Provider
    ai_default_provider_id = fields.Many2one(
        'ai.provider',
        string='Default AI Provider',
        config_parameter='hp_ai_base.default_provider_id'
    )

    # AI Bot Configuration
    ai_bot_partner_id = fields.Many2one(
        'res.partner',
        string='AI Bot Partner',
        config_parameter='hp_ai_base.ai_bot_partner_id',
        help='The partner used for AI bot messages in chatter'
    )

    # Feature Toggles
    ai_enable_logging = fields.Boolean(
        string='Enable Usage Logging',
        config_parameter='hp_ai_base.enable_logging',
        default=True
    )
    ai_enable_cost_tracking = fields.Boolean(
        string='Enable Cost Tracking',
        config_parameter='hp_ai_base.enable_cost_tracking',
        default=True
    )

    # Rate Limiting
    ai_global_rate_limit = fields.Integer(
        string='Global Rate Limit (requests/min)',
        config_parameter='hp_ai_base.global_rate_limit',
        default=100
    )

    @api.model
    def get_ai_bot_partner(self):
        """Get the AI Bot partner for posting messages"""
        param = self.env['ir.config_parameter'].sudo()
        partner_id = param.get_param('hp_ai_base.ai_bot_partner_id')
        if partner_id:
            return self.env['res.partner'].browse(int(partner_id))
        # Fallback to creating one if not exists
        return self._ensure_ai_bot_partner()

    @api.model
    def _ensure_ai_bot_partner(self):
        """Ensure AI Bot partner exists"""
        partner = self.env.ref('hp_ai_base.partner_ai_bot', raise_if_not_found=False)
        if not partner:
            partner = self.env['res.partner'].sudo().create({
                'name': 'AI Assistant',
                'email': 'ai-bot@localhost',
                'is_company': False,
                'type': 'contact',
                'image_1920': False,  # Can set a default avatar here
            })
            # Store the reference
            self.env['ir.config_parameter'].sudo().set_param(
                'hp_ai_base.ai_bot_partner_id', str(partner.id)
            )
        return partner
