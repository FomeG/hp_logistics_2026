from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import date

class ProductTemplateInherit(models.Model):
    _inherit = "product.template"
    _order = 'create_date desc'

    route_id = fields.Many2one(
        'freight.purchase.route',
        string='Route',
        tracking=True
    )
    freight_booking_id = fields.Many2one(
        'freight.purchase.booking', 
        string='Booking',
        domain="[('etd', '>', '{}')]".format(date.today()),
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('type') == 'pricing' and not (
                self.env.context.get('create_from_route') or 
                self.env.context.get('create_from_pol_pod')  # Keep backward compatibility
            ):
                raise ValidationError(_("You cannot create 'Pricing' products manually."))
        return super(ProductTemplateInherit, self).create(vals_list)



