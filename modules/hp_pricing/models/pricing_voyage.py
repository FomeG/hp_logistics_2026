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
    pol_id = fields.Many2one(
        'pricing.pol', string="Port of Loading",
        tracking=True
    )
    pod_id = fields.Many2one(
        'pricing.pod', string="Port of Discharge",
        domain=lambda self: self._get_pod_domain(),
        tracking=True
    )

    # display_name
    @api.depends('shipping_vessel_id.vessel_name', 'voyage_no')
    def _compute_display_name(self):
        for record in self:
            vessel = record.shipping_vessel_id.vessel_name if record.shipping_vessel_id else "Unknown Vessel"
            voyage = record.voyage_no if record.voyage_no else "Unknown Voyage"
            record.display_name = f"{vessel} {voyage}"

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

    @api.model
    def create(self, vals):
        """Prevent voyage creation if the user has no assigned region or is not in any pricing team"""
        user = self.env.user
        pricing_member = self.env['pricing.team.member'].search([('user_id', '=', user.id)], limit=1)

        if not user.region_id:
            raise UserError(_("You have no region assigned. Please contact the administrator."))

        if not pricing_member:
            raise UserError(_("You are not assigned to any Pricing Team. Please contact the administrator."))

        return super(PricingVoyage, self).create(vals)
