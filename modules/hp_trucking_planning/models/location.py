from odoo import models, fields, api


class Location(models.Model):
    _name = 'trucking_planning.location'
    _description = 'Location'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    type = fields.Selection([
        ('container_pickup', 'Container Pickup'),
        ('goods_pickup_delivery', 'Goods Pickup/Delivery'),
        ('container_delivery', 'Container Delivery'),
        ('port', 'Port'),
        ('warehouse', 'Warehouse'),
        ('factory', 'Factory'),
        ('other', 'Other')
    ], required=True, tracking=True)
    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
    )
    extra_fuel = fields.Boolean(
        string="Extra Fuel",
        default=False,
        tracking=True,
    )
    address = fields.Char(
        string="Address",
        tracking=True,
    )
    contact_phone = fields.Char(
        string="Contact Phone",
        tracking=True,
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        readonly=True
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string='Province',
        domain="[('country_id.code', '=', 'VN')]",
        index=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(Location, self).default_get(fields)
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        if country:
            res['country_id'] = country.id
        return res
