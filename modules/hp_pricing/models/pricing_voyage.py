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
        # default=lambda self: self.env['pricing.team.member'].search([('user_id', '=', self.env.user.id)], limit=1),
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
            existing_voyage = self.env['pricing.voyage'].search([
                ('display_name', 'ilike', record.display_name),
                ('id', '!=', record.id)  # Exclude self when updating
            ])
            if existing_voyage:
                raise ValidationError(_("The Voyage '%s' already exists.") % record.display_name)

    # @api.model
    # def _get_pod_domain(self):
    #     """Return the domain for POD selection based on user region"""
    #     user = self.env.user
    #     if user.region_id:
    #         return [('region_id', '=', user.region_id.id)]
    #     else:
    #         return []  # Empty domain if no region assigned

    @api.onchange('sealine_id')
    def _onchange_sealine_id(self):
        # Clear pricing_member_id when sealine changes
        self.pricing_member_id = False

        user = self.env.user
        sealine = self.sealine_id
        region = sealine.pod_id.region_id if sealine.pod_id else False
        is_director = user.has_group('hp_pricing.group_hp_pricing_director')

        if not self.sealine_id or not region:
            return {'domain': {'pricing_member_id': [('id', '=', False)]}}

        # Find active pricing team members assigned to this region
        members = self.env['pricing.team.member'].sudo().search([
            ('region_id', '=', region.id),
            ('active', '=', True)
        ])

        if is_director:
            # DIRECTOR: Show all suitable pricing members for the region
            if members:
                # Set the first available member as default
                self.pricing_member_id = members[0]
                return {'domain': {'pricing_member_id': [('id', 'in', members.ids)]}}
            else:
                # No members found - create pricing member for current director
                pricing_member = self._get_or_create_pricing_member_for_current_user(user, region)
                if pricing_member:
                    self.pricing_member_id = pricing_member
                    return {'domain': {'pricing_member_id': [('id', '=', pricing_member.id)]}}
        else:
            # NON-DIRECTOR: Show only current user as pricing member
            # Check if current user has pricing member for this region
            current_user_member = self.env['pricing.team.member'].sudo().search([
                ('user_id', '=', user.id),
                ('region_id', '=', region.id),
                ('active', '=', True)
            ], limit=1)

            if current_user_member:
                # Current user already has pricing member for this region
                self.pricing_member_id = current_user_member
                return {'domain': {'pricing_member_id': [('id', '=', current_user_member.id)]}}
            else:
                # Create pricing member for current user in this region
                pricing_member = self._get_or_create_pricing_member_for_current_user(user, region)
                if pricing_member:
                    self.pricing_member_id = pricing_member
                    return {'domain': {'pricing_member_id': [('id', '=', pricing_member.id)]}}

                return {'domain': {'pricing_member_id': [('id', '=', False)]}}


    def _get_or_create_pricing_member_for_current_user(self, user, region=False):
        """Get or create pricing member for current user and assign to region if provided"""
        # Find existing pricing team for this user
        pricing_team = self.env['pricing.team'].sudo().search([
            ('team_manager_id', '=', user.id)
        ], limit=1)

        if not pricing_team:
            pricing_team = self.env['pricing.team'].sudo().create({
                'name': f"{user.name}'s Pricing Team",
                'team_manager_id': user.id,
                'active': True,
            })

        # Find existing pricing member
        pricing_member = self.env['pricing.team.member'].sudo().search([
            ('user_id', '=', user.id),
            ('pricing_team_id', '=', pricing_team.id),
            ('active', '=', True)
        ], limit=1)

        if not pricing_member:
            # Create new pricing member
            pricing_member = self.env['pricing.team.member'].sudo().create({
                'user_id': user.id,
                'pricing_team_id': pricing_team.id,
                'region_id': region.id if region else False,
                'active': True
            })
        else:
            # Update existing pricing member with region if provided and not already set
            if region and not pricing_member.region_id:
                pricing_member.write({'region_id': region.id})

        return pricing_member

    @api.model_create_multi
    def create(self, vals_list):
        """Create method that handles batch creation properly"""
        user = self.env.user
        is_director = user.has_group('hp_pricing.group_hp_pricing_director')

        # Process each record in the batch
        for vals in vals_list:
            sealine_id = vals.get('sealine_id')
            pricing_member_id = vals.get('pricing_member_id')

            # If pricing_member_id is not provided, determine it based on sealine
            if not pricing_member_id and sealine_id:
                sealine = self.env['pricing.sealine'].browse(sealine_id)
                region = sealine.pod_id.region_id if sealine.pod_id else False

                if region:
                    if is_director:
                        # DIRECTOR: Try to find any active pricing team member for the region
                        pricing_member = self.env['pricing.team.member'].search([
                            ('region_id', '=', region.id),
                            ('active', '=', True)
                        ], limit=1)

                        if pricing_member:
                            vals['pricing_member_id'] = pricing_member.id
                        else:
                            # No members found - create pricing member for current director
                            pricing_member = self._get_or_create_pricing_member_for_current_user(user, region)
                            if pricing_member:
                                vals['pricing_member_id'] = pricing_member.id
                    else:
                        # NON-DIRECTOR: Look for current user's pricing member for this region
                        pricing_member = self.env['pricing.team.member'].search([
                            ('user_id', '=', user.id),
                            ('region_id', '=', region.id),
                            ('active', '=', True)
                        ], limit=1)

                        if pricing_member:
                            vals['pricing_member_id'] = pricing_member.id
                        else:
                            # Create pricing member for current user in this region
                            pricing_member = self._get_or_create_pricing_member_for_current_user(user, region)
                            if pricing_member:
                                vals['pricing_member_id'] = pricing_member.id

            # Validation: Ensure pricing_member_id is set
            if not vals.get('pricing_member_id'):
                # For any user without pricing member, create one
                pricing_member = self._get_or_create_pricing_member_for_current_user(user)
                if pricing_member:
                    vals['pricing_member_id'] = pricing_member.id
                else:
                    raise UserError(_("Unable to create pricing member. Please contact the administrator."))

        return super(PricingVoyage, self).create(vals_list)