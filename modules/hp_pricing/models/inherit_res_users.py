from odoo import api, fields, models

def get_excluded_user_ids(env):
    excluded_user_ids = set()

    high_level_users = env['res.users'].search([
        ('groups_id', 'in', [env.ref('hr_recruitment.group_hr_recruitment_manager').id])
    ])
    excluded_user_ids.update(high_level_users.ids)

    ceo_pattern_users = env['res.users'].search([
        '|', '|',
        ('login', 'ilike', 'ceo'),
        ('login', 'ilike', 'admin'),
        ('email', 'ilike', 'ceo')
    ])
    excluded_user_ids.update(ceo_pattern_users.ids)

    return list(excluded_user_ids)

class ResUsers(models.Model):
    _inherit = 'res.users'

    region_id = fields.Many2one('pricing.region', string='Region')
    pricing_team_ids = fields.Many2many(
        'pricing.team', 'pricing_team_member', 'user_id', 'pricing_team_id',
        compute='_compute_pricing_team_ids', search='_search_pricing_team_ids'
    )
    pricing_team_member_ids = fields.One2many(
        'pricing.team.member', 'user_id', string='Pricing Team Memberships'
    )

    pricing_team_id = fields.Many2one(
        'pricing.team', string='User Pricing Team', compute='_compute_pricing_team_id',
        readonly=True, store=True,
        help="Main user pricing team. Used to identify the primary pricing team for this user."
    )

    @api.depends('pricing_team_member_ids.active')
    def _compute_pricing_team_ids(self):
        for user in self:
            user.pricing_team_ids = user.pricing_team_member_ids.pricing_team_id

    def _search_pricing_team_ids(self, operator, value):
        return [('pricing_team_member_ids.pricing_team_id', operator, value)]

    @api.depends('pricing_team_member_ids.pricing_team_id', 'pricing_team_member_ids.create_date',
                 'pricing_team_member_ids.active')
    def _compute_pricing_team_id(self):
        for user in self:
            if not user.pricing_team_member_ids:
                user.pricing_team_id = False
            else:
                active_memberships = user.pricing_team_member_ids.filtered(lambda m: m.active)
                user.pricing_team_id = active_memberships.sorted('create_date', reverse=True)[:1].pricing_team_id if active_memberships else False

