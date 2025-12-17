from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    is_base_currency = fields.Boolean(
        string='Is Base Currency',
        default=False,
        help="Indicates if this currency is the base currency for the custom logic.",
    )

    @api.constrains('is_base_currency')
    def _check_single_base_currency(self):
        """Ensure only one currency is set as base currency."""
        for record in self:
            if record.is_base_currency:
                # Search for other currencies that are marked as base
                other_base = self.search([
                    ('is_base_currency', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_base:
                    raise ValidationError(_('Only one currency can be set as base currency!'))

    @api.model
    def get_base_currency(self):
        """Lấy đồng tiền được cấu hình là Base Currency. Nếu không tìm thấy cái nào được tick, mới fallback về tiền tệ của công ty."""
        base = self.search([('is_base_currency', '=', True)], limit=1)
        if base:
            return base
        return self.env.company.currency_id