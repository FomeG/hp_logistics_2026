from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    trucking_team_ids = fields.Many2many(
        'trucking.team', 'trucking_team_member', 'user_id', 'trucking_team_id',
        compute='_compute_trucking_team_ids', search='_search_trucking_team_ids'
    )
    trucking_team_member_ids = fields.One2many(
        'trucking.team.member', 'user_id', string='Trucking Team Memberships'
    )

    trucking_team_id = fields.Many2one(
        'trucking.team', string='User Trucking Team', compute='_compute_trucking_team_id',
        readonly=True, store=True,
        help="Main user trucking team. Used to identify the primary pricing team for this user."
    )

    # Trucking
    @api.depends('trucking_team_member_ids.active')
    def _compute_trucking_team_ids(self):
        for user in self:
            user.trucking_team_ids = user.trucking_team_member_ids.trucking_team_id

    def _search_trucking_team_ids(self, operator, value):
        return [('trucking_team_member_ids.trucking_team_id', operator, value)]

    @api.depends('trucking_team_member_ids.trucking_team_id', 'trucking_team_member_ids.create_date',
                 'trucking_team_member_ids.active')
    def _compute_trucking_team_id(self):
        for user in self:
            if not user.trucking_team_member_ids:
                user.trucking_team_id = False
            else:
                active_memberships = user.trucking_team_member_ids.filtered(lambda m: m.active)
                user.trucking_team_id = active_memberships.sorted('create_date', reverse=True)[
                                       :1].trucking_team_id if active_memberships else False

