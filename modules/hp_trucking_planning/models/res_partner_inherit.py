from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..services.res_partner_service import ResPartnerService

class ResPartnerInherit(models.Model):
    _inherit = ['res.partner']

    type = fields.Selection([
        ('contact', 'Contact'),
        ('invoice', 'Invoice Address'),
        ('delivery', 'Delivery Address'),
        ('other', 'Other Address'),
        (ResPartnerService.PARTNER_TYPE_DRIVER, 'Driver'),
        (ResPartnerService.PARTNER_TYPE_CLIENT, 'Client'),
    ],string='Address Type', default='contact')

    cccd = fields.Char(string='CCCD', tracking=True)
    code = fields.Char(string= 'Client Code', tracking=True)
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
        ResPartnerService.PARTNER_TYPE_CLIENT: ['name', 'code', 'vat', 'branch_id'],
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
