from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

import logging

_logger = logging.getLogger(__name__)

class PricingVoyage(models.Model):
    _name = 'pricing.voyage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Pricing Voyage'
    _rec_name = 'display_name'
    _order = 'write_date desc'

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )

    shipping_vessel_id = fields.Many2one(
        'pricing.shipping.vessel', string="Tàu hàng",
        tracking=True
    )
    voyage_no = fields.Char(string='Voyage No', tracking=True)
    shipping_line_id = fields.Many2one(
        'pricing.shipping.line', string="Shipping Line",
        tracking=True
    )
    etd = fields.Date(
        string="Estimate Departure",
        help="Estimate Departure"
    )
    pricing_member_id = fields.Many2one(
        'pricing.team.member', string="Pricing Member",
        default=lambda self: self.env['pricing.team.member'].search([('user_id', '=', self.env.user.id)], limit=1),
        tracking=True
    )
    sealine_id = fields.Many2one(
        'pricing.sealine', string="Sealine",
        tracking=True
    )

    # display_name
    @api.depends('shipping_vessel_id.vessel_name', 'voyage_no', 'sealine_id')
    def _compute_display_name(self):
        for record in self:
            vessel = record.shipping_vessel_id.vessel_name if record.shipping_vessel_id else "Unknown Vessel"
            voyage = record.voyage_no if record.voyage_no else "Unknown Voyage"
            record.display_name = f"{vessel} {voyage} for route: {record.sealine_id.sealine_name}"

    @api.constrains('display_name')
    def _check_unique_display_name(self):
        """ Ensure unique display_name """
        for record in self:
            existing_voyage = self.env['pricing.shipping.vessel'].search([
                ('display_name', 'ilike', record.display_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_voyage:
                raise ValidationError(_("The Voyage '%s' already exists.") % record.display_name)

    @api.model
    def _get_pod_domain(self):
        """Return the domain for POD selection based on user region"""
        user = self.env.user
        if user.region_id:
            return [('region_id', '=', user.region_id.id)]
        else:
            return []  # Empty domain if no region assigned

    @api.onchange('pricing_member_id')
    def _onchange_pricing_member_id(self):
        if self.env.user.has_group('hp_pricing.group_hp_pricing_director') and not self.sealine_id:
            self.pricing_member_id = False  # reset
            return {
                'warning': {
                    'title': _("Missing Sealine"),
                    'message': _("Please select a Sealine before choosing a Pricing Member.")
                }
            }

    @api.model
    def create(self, vals):
        user = self.env.user
        is_director = user.has_group('hp_pricing.group_hp_pricing_director')

        sealine_id = vals.get('sealine_id')
        pricing_member = None

        # Validation: If user is director, sealine is required
        if is_director and not sealine_id:
            raise UserError(_("Please select a Sealine before creating a voyage."))

        if is_director and sealine_id:
            sealine = self.env['pricing.sealine'].browse(sealine_id)
            region = sealine.pod_id.region_id

            # Try to find active pricing team members assigned to the region
            pricing_member = self.env['pricing.team.member'].search([
                ('region_id', '=', region.id),
                ('active', '=', True)
            ], limit=1)

            # If region has no member OR sealine is new (no region found), assign director
            if not pricing_member:
                # Find a team where the user is already manager
                pricing_team = self.env['pricing.team'].search([
                    ('team_manager_id', '=', user.id)
                ], limit=1)

                if not pricing_team:
                    # If no such team, create a new one
                    pricing_team = self.env['pricing.team'].create({
                        'name': f"{user.name}'s Pricing Team",
                        'team_manager_id': user.id,
                        'active': True,
                    })

                # Now add user as a team member if not already
                pricing_member = self.env['pricing.team.member'].search([
                    ('user_id', '=', user.id),
                    ('pricing_team_id', '=', pricing_team.id)
                ], limit=1)

                if not pricing_member:
                    pricing_member = self.env['pricing.team.member'].create({
                        'user_id': user.id,
                        'pricing_team_id': pricing_team.id,
                        'active': True
                    })

        # Fallback: not a director → default behavior
        elif not is_director:
            pricing_member = self.env['pricing.team.member'].search([
                ('user_id', '=', user.id)
            ], limit=1)

            if not user.region_id:
                raise UserError(_("You have no region assigned. Please contact the administrator."))

            if not pricing_member:
                raise UserError(_("You are not assigned to any Pricing Team. Please contact the administrator."))

        # Set the pricing member
        vals.setdefault('pricing_member_id', pricing_member.id)

        return super(PricingVoyage, self).create(vals)

