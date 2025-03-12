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
        domain="['&', ('share', '=', False), ('company_ids', 'in', member_company_ids)]",
        compute='_compute_member_ids', inverse='_inverse_member_ids', search='_search_member_ids',
        help="Users assigned to this Pricing Team."
    )

    member_company_ids = fields.Many2many(
        'res.company', compute='_compute_member_company_ids',
        help='Available companies for user assignment.'
    )

    @api.depends('pricing_team_member_ids.active')
    def _compute_member_ids(self):
        for team in self:
            team.member_ids = team.pricing_team_member_ids.user_id

    def _inverse_member_ids(self):
        for team in self:
            memberships = team.pricing_team_member_ids
            users_current = team.member_ids
            users_new = users_current - memberships.user_id

            user_team_ids = [{'user_id': user.id, 'pricing_team_id': team.id} for user in users_new]
            self.env['pricing.team.member']._synchronize_memberships(user_team_ids)

            self.env['pricing.team.member'].create(user_team_ids)

            for membership in memberships:
                membership.active = membership.user_id in users_current

    def _search_member_ids(self, operator, value):
        return [('pricing_team_member_ids.user_id', operator, value)]

    @api.depends('company_id')
    def _compute_member_company_ids(self):
        all_companies = self.env['res.company'].search([])
        for team in self:
            team.member_company_ids = team.company_id or all_companies

    @api.model_create_multi
    def create(self, vals_list):
        teams = super(PricingTeam, self).create(vals_list)
        return teams

    def write(self, values):
        res = super(PricingTeam, self).write(values)
        return res
