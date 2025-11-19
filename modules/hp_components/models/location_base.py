from odoo import models, fields, api
from odoo.exceptions import ValidationError

class LocationBase(models.Model):
    _name = 'location.base'
    _description = 'Location'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    type = fields.Selection([
        ('container_pickup', 'Container Pickup'),
        ('goods_pickup_delivery', 'Goods Pickup/Delivery'),
        ('container_delivery', 'Container Delivery'),
        ('route_point', 'Route Point'),
        ('port', 'Port'),
        ('depot', 'Depot'),  # Bãi chứa container, thường nằm trong cảng
        ('warehouse', 'Warehouse'),
        ('factory', 'Factory'),
        ('other', 'Other')
    ], required=True, tracking=True)

    name = fields.Char(
        string="Name",
        required=True,
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
        readonly=False
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string='Province',
        domain="""[
                   '&',
                   ('country_id.code', '=', 'VN'),
                   ('name_unaccent', 'ilike', unaccent(%(user_input)s))
               ]""",
        index=True,
    )

    latitude = fields.Float(
        string="Latitude",
        digits=(10, 7),
        help="Latitude coordinate (-90 to 90)"
    )

    longitude = fields.Float(
        string="Longitude",
        digits=(10, 7),
        help="Longitude coordinate (-180 to 180)"
    )

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Validate tọa độ"""
        for record in self:
            if record.latitude and not -90 <= record.latitude <= 90:
                raise ValidationError('Latitude phải nằm trong khoảng -90 đến 90.')
            if record.longitude and not -180 <= record.longitude <= 180:
                raise ValidationError('Longitude phải nằm trong khoảng -180 đến 180.')

    @api.model
    def default_get(self, fields_list):
        """Set default country to Vietnam"""
        res = super(LocationBase, self).default_get(fields_list)
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        if country:
            res['country_id'] = country.id
        return res