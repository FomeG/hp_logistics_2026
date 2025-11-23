from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

class LocationBase(models.Model):
    _name = 'location.base'
    _description = 'Location'
    _inherit = ['unique.code.mixin', 'unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    type = fields.Selection(
        constants.LocationType.SELECT_OPTIONS,
        required=True,
        tracking=True,
        default=constants.LocationType.PORT
    )

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
    extra_fuel = fields.Boolean(
        string="Extra Fuel",
        default=False,
        tracking=True,
    )

    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string='Province',
        index=True,
        domain="[('country_id', '=?', country_id)]",
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
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

    region_id = fields.Many2one(
        comodel_name="region",
        related='country_id.region_id',
        string='Region',
        store=False,
    )
    country_str = fields.Char(
        string="Zone",
        compute='_compute_country_str',
    )
    is_local =fields.Boolean(
        string="Is Local",
        compute='_compute_is_local',
        store=False,
        readonly=True,
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
        res = super(LocationBase, self).default_get(fields_list)
        country = self.env['res.country'].search([('code', '=', 'VN')], limit=1)
        if country:
            res['country_id'] = country.id
        return res

    def _compute_country_str(self):
        for record in self:
            record.country_str = f"{record.country_id.name} ({record.country_id.region_id.name})"

    def _compute_is_local(self):
        vietnam = self.env['hp_components.geo.service'].get_vietnam()
        if not vietnam:
            raise ValidationError('VN does not exists in DB')
        for record in self:
            record.is_local = record.country_id.id == vietnam.id
