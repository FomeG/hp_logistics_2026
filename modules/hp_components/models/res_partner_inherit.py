from odoo import models, fields ,api
from odoo.addons.hp_components.models import constants

from odoo.exceptions import ValidationError
from ..validators.shipping_line_validator import ShippingLineValidator

from odoo.api import ValuesType, Self


class ResPartnerInherit(models.Model):
    _inherit = ['res.partner']
    _description = 'Res Partner Inherit'

    partner_main_type_id = fields.Many2one(
        comodel_name='partner.main.type',
        string='Main Partner Type',
        index=True,
    )
    is_shipping_line = fields.Boolean(
        compute="_compute_is_shipping_line",
        store=False
    )
    @api.depends('partner_main_type_id')
    def _compute_is_shipping_line(self):
        for rec in self:
            rec.is_shipping_line = (rec.partner_main_type_id.code == constants.PartnerMainTypeCode.SHIPPING_LINE)

    @api.model_create_multi
    def create(self, vals_list: list[ValuesType]) -> Self:
        partner_main_type = self.env['hp_components.partner.service'].get_partner_main_type_shipping_line()
        if not partner_main_type:
            raise ValidationError("Partner main type not found")
        for vals in vals_list:
            if vals.get('partner_main_type_id') and vals.get('partner_main_type_id') == partner_main_type.id:
                validated, errors = ShippingLineValidator.validate_create(vals, self.env)
                if errors:
                    raise ValidationError("\n".join([f"• {e}" for e in errors]))

        return super(ResPartnerInherit, self).create(vals_list)

    def write(self, vals: dict) -> dict:
        for record in self:
            inputs = vals.copy()
            inputs['current_id'] = record.id
            validated, errors = ShippingLineValidator.validate_update(inputs, self.env, record)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super(ResPartnerInherit, self).write(vals)
