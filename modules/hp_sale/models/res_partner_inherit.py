from odoo import models, api, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    branch_id = fields.Many2one(
        comodel_name='hr.branch',
        string='Sales Branch',
        index=True,
    )
    address_display = fields.Char(
        string='Address Display',
        compute='_compute_address_display',
        store=False,
    )

    def _compute_address_display(self):
        for partner in self:
            address_parts = [
                partner.street or '',
                partner.street2 or '',
                partner.city or '',
                partner.state_id.name if partner.state_id else '',
                partner.zip or '',
                partner.country_id.name if partner.country_id else ''
            ]
            # Filter out empty parts and join with commas
            partner.address_display = ', '.join(filter(None, address_parts))
