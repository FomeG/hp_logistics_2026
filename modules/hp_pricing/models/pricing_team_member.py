from odoo import api, fields, models, exceptions, _


class PricingTeamMember(models.Model):
    _name = 'pricing.team.member'
    _inherit = ['mail.thread']
    _description = 'Pricing Team Member'
    _rec_name = 'user_id'
    _order = 'create_date ASC, id'

    pricing_team_id = fields.Many2one(
        'pricing.team', string='Pricing Team',
        required=True, ondelete="cascade"
    )
    user_id = fields.Many2one(
        'res.users', string='Pricing User',
        required=True, ondelete='cascade'
    )
    region_id = fields.Many2one(
        'pricing.region', string='Managed Regions'
    )
    active = fields.Boolean(default=True)

    @api.constrains('pricing_team_id', 'user_id', 'active')
    def _check_duplicate_membership(self):
        existing = self.search([
            ('pricing_team_id', '=', self.pricing_team_id.id),
            ('user_id', '=', self.user_id.id),
            ('active', '=', True)
        ])
        if len(existing) > 1:
            raise exceptions.ValidationError("This user is already an active member of this Pricing Team.")

    def _synchronize_memberships(self, user_team_ids):
        is_membership_multi = self.env['ir.config_parameter'].sudo().get_param('pricing_team.membership_multi', False)

        if not is_membership_multi:
            existing = self.search([
                ('active', '=', True),
                ('user_id', 'in', [values['user_id'] for values in user_team_ids])
            ])
            memberships_to_archive = existing.filtered(
                lambda m: m.pricing_team_id.id not in [values['pricing_team_id'] for values in user_team_ids]
            )
            if memberships_to_archive:
                memberships_to_archive.write({'active': False})

    @api.model_create_multi
    def create(self, vals_list):
        self._synchronize_memberships(vals_list)
        return super(PricingTeamMember, self).create(vals_list)

    def write(self, values):
        if values.get('active'):
            self._synchronize_memberships(
                [{'user_id': m.user_id.id, 'pricing_team_id': m.pricing_team_id.id} for m in self])
        return super(PricingTeamMember, self).write(values)
