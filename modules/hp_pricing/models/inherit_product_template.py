from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date

PRICING_GROUPS = [
    'your_module.pricing_group',
    'your_module.another_group',
    'your_module.yet_another_group',
]

class ProductTemplate(models.Model):
    _inherit = "product.template"

    sealine_id = fields.Many2one(
        'pricing.sealine', string="Sealine",
        tracking=True
    )
    booking_id = fields.Many2one(
        'pricing.booking', string="Booking",
        domain="[('voyage_id.etd', '>', '{}')]".format(date.today()),
        tracking=True
    )

    def write(self, vals):
        restricted = self.filtered(lambda p: p.type == 'pricing')
        if restricted and not (
                self.env.user.has_group('hp_pricing.group_hp_pricing_member') or
                self.env.user.has_group('hp_pricing.group_hp_pricing_lead') or
                self.env.user.has_group('hp_pricing.group_hp_pricing_director') or
                self.env.user.has_group('hp_pricing.group_hp_pricing_administrator')
        ):
            raise ValidationError(_("Only Pricing members can edit 'Pricing' products."))
        return super(ProductTemplate, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type') == 'pricing' and not self.env.context.get('create_from_pol_pod'):
                raise ValidationError(_("You cannot create 'Pricing' products manually."))
        return super(ProductTemplate, self).create(vals_list)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'pricing' and not (
                self.env.user.has_group('sale.group_hp_pricing_member') or
                self.env.user.has_group('sale.group_hp_pricing_lead') or
                self.env.user.has_group('sale.group_hp_pricing_director') or
                self.env.user.has_group('sale.group_hp_pricing_administrator')
        ):
            raise UserError(_("You do not have permission to create or edit 'Pricing' type products."))