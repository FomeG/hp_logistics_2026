from odoo import api, fields, models, exceptions, _


class PricingTeam(models.Model):
    _name = "pricing.team"
    _inherit = ['mail.thread']
    _description = "Pricing Team"
    _order = "sequence ASC, create_date DESC, id DESC"

    name = fields.Char('Pricing Team Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True)
    team_manager_id = fields.Many2one(
        'res.users', string='Pricing Team Manager',
        domain="[('share', '=', False)]",
        help="The manager responsible for this Pricing Team."
    )

    pricing_team_member_ids = fields.One2many(
        'pricing.team.member', 'pricing_team_id',
        string='Pricing Team Members', context={'active_test': True}
    )

    member_ids = fields.Many2many(
        'res.users', string='Pricing Team Users',
        domain="[('id', 'not in', assigned_user_ids), ('groups_id', 'in', pricing_group_ids)]",
        compute='_compute_member_ids', inverse='_inverse_member_ids', search='_search_member_ids',
        help="Users assigned to this Pricing Team."
    )

    assigned_user_ids = fields.Many2many(
        'res.users', compute='_compute_assigned_users', store=False
    )

    pricing_group_ids = fields.Many2many(
        'res.groups', compute='_compute_pricing_groups', store=False
    )


    @api.depends('pricing_team_member_ids.active')
    def _compute_member_ids(self):
        for team in self:
            team.member_ids = team.pricing_team_member_ids.user_id

    def _inverse_member_ids(self):
        for team in self:
            memberships = team.pricing_team_member_ids
            users_current = team.member_ids

            # Archive memberships for users no longer in the team
            memberships_to_archive = memberships.filtered(lambda m: m.user_id not in users_current)
            if memberships_to_archive:
                memberships_to_archive.write({'active': False})

            # Create new memberships for new users
            users_new = users_current - memberships.filtered(lambda m: m.active).user_id
            if users_new:
                user_team_ids = [{'user_id': user.id, 'pricing_team_id': team.id} for user in users_new]
                self.env['pricing.team.member'].create(user_team_ids)
    
    def _search_member_ids(self, operator, value):
        return [('pricing_team_member_ids.user_id', operator, value)]

    @api.depends('pricing_team_member_ids.user_id')
    def _compute_assigned_users(self):
        """ Compute users who are already assigned to a pricing team. """
        all_users = self.env['pricing.team.member'].search([]).mapped('user_id')
        for team in self:
            team.assigned_user_ids = all_users

    @api.depends()
    def _compute_pricing_groups(self):
        """ Compute Pricing Groups """
        pricing_group_refs = [
            'hp_pricing.group_hp_pricing_member',
            'hp_pricing.group_hp_pricing_lead',
            'hp_pricing.group_hp_pricing_director',
            'hp_pricing.group_hp_pricing_administrator'
        ]
        self.pricing_group_ids = self.env['res.groups'].browse([
            self.env.ref(ref).id for ref in pricing_group_refs if self.env.ref(ref, raise_if_not_found=False)
        ])



