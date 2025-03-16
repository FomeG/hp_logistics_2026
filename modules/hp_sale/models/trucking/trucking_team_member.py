from odoo import api, fields, models, exceptions, _


class TruckingTeamMember(models.Model):
    _name = 'trucking.team.member'
    _inherit = ['mail.thread']
    _description = 'Trucking Team Member'
    _rec_name = 'user_id'
    _order = 'create_date ASC, id'

    trucking_team_id = fields.Many2one(
        'trucking.team', string='Trucking Team',
        required=True, ondelete="cascade"
    )
    user_id = fields.Many2one(
        'res.users', string='Trucking User',
        required=True, ondelete='cascade'
    )
    active = fields.Boolean(default=True)

    @api.constrains('trucking_team_id', 'user_id', 'active')
    def _check_duplicate_membership(self):
        existing = self.search([
            ('trucking_team_id', '=', self.trucking_team_id.id),
            ('user_id', '=', self.user_id.id),
            ('active', '=', True)
        ])
        if len(existing) > 1:
            raise exceptions.ValidationError("This user is already an active member of this Trucking Team.")

    def _synchronize_memberships(self, user_team_ids):
        is_membership_multi = self.env['ir.config_parameter'].sudo().get_param('trucking_team.membership_multi', False)

        if not is_membership_multi:
            existing = self.search([
                ('active', '=', True),
                ('user_id', 'in', [values['user_id'] for values in user_team_ids])
            ])
            memberships_to_archive = existing.filtered(
                lambda m: m.trucking_team_id.id not in [values['trucking_team_id'] for values in user_team_ids]
            )
            if memberships_to_archive:
                memberships_to_archive.write({'active': False})

    @api.model_create_multi
    def create(self, vals_list):
        self._synchronize_memberships(vals_list)
        return super(TruckingTeamMember, self).create(vals_list)

    def write(self, values):
        if values.get('active'):
            self._synchronize_memberships(
                [{'user_id': m.user_id.id, 'trucking_team_id': m.trucking_team_id.id} for m in self])
        return super(TruckingTeamMember, self).write(values)
