from odoo import models, fields, api


class ResPartnerClient(models.Model):
    _inherit = ['res.partner.client']

    is_monthly_billing = fields.Boolean(
        string="Monthly Billing",
        default=False,
        help="If checked, CS orders from this client will be grouped into monthly batch orders",
        tracking=True,
    )
    cs_member_id = fields.Many2one(
        comodel_name='res.users',
        string="CS Member",
        help="CS Member assigned to this client. CS orders will be automatically assigned to this member.",
        domain=lambda self: self._get_cs_member_domain(),
        tracking=True,
    )

    def _get_cs_member_domain(self):
        """Return domain to filter users with CS member group"""
        cs_member_group = self.env.ref('hp_customer_service.group_hp_customer_service_member', raise_if_not_found=False)
        if cs_member_group:
            return [('groups_id', 'in', [cs_member_group.id])]
        return []