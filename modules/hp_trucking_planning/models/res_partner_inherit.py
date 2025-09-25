from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..services.res_partner_service import ResPartnerService

class ResPartnerInherit(models.Model):
    _inherit = ['res.partner']

    # Extend existing selection instead of redefining it to avoid overwriting core values
    type = fields.Selection(selection_add=[
        (ResPartnerService.PARTNER_TYPE_DRIVER, 'Driver'),
        (ResPartnerService.PARTNER_TYPE_CLIENT, 'Client'),
        (ResPartnerService.DRIVER_INTERNAL_TYPE, 'Internal Driver'),
        (ResPartnerService.DRIVER_EXTERNAL_TYPE, 'External Driver'),
        (ResPartnerService.SHIPPING_LINE, 'Shipping Line'),
    ])
    cccd = fields.Char(string='CCCD', tracking=True)
    branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        string='Branch',
        tracking=True,
        default=lambda self: self.env.user.branch_ids[:1].id,
    )

    _sql_constraints = [
        ('unique_cccd', 'UNIQUE(cccd)', 'CCCD must be unique!'),
        ('unique_vat', 'UNIQUE(vat)','Tax Number must be unique!'),
    ]

    _required_fields_by_type = {
        ResPartnerService.PARTNER_TYPE_DRIVER: ['name', 'cccd'],
        ResPartnerService.PARTNER_TYPE_CLIENT: ['name', 'ref', 'vat', 'branch_id'],
    }

    @api.constrains('type')
    def _check_required_fields_by_type(self):
        for rec in self:
            required_fields = self._required_fields_by_type.get(rec.type, [])
            missing = [field for field in required_fields if not rec[field]]
            if missing:
                raise ValidationError(
                    f"When type is '{rec.type}', the following fields are required: {', '.join(missing)}"
                )
