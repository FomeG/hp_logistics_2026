from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants
import re

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
    contact_name = fields.Char(
        string="Contact Name",
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
        required=True,
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
        store=True,
        readonly=True,
    )
    parent_id = fields.Many2one(
        comodel_name='location.base',
        string='Parent Location',
        ondelete='set null',
    )
    children_ids = fields.One2many(
        comodel_name='location.base',
        inverse_name='parent_id',
        string='Child Locations',
    )

    source = fields.Selection(
        selection=constants.LocationSource.SELECT_OPTIONS,
        string='Source',
        default=constants.LocationSource.MANUAL,
    )

    @api.constrains('contact_phone')
    def _check_contact_phone(self):
        """Kiểm tra định dạng số điện thoại"""
        for record in self:
            if record.contact_phone:
                pattern = r'^[0-9+\s().-]+$'
                if not re.match(pattern, record.contact_phone):
                    raise ValidationError(
                        _("Số điện thoại liên hệ không hợp lệ. Vui lòng chỉ sử dụng số và các ký tự đặc biệt hỗ trợ (+, -, ...)."))

                digits_only = re.sub(r'\D', '', record.contact_phone)
                if len(digits_only) < 9 or len(digits_only) > 15:
                    raise ValidationError(_("Số điện thoại phải có độ dài từ 9 đến 15 chữ số."))

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
    @api.depends('country_id')
    def _compute_is_local(self):
        vietnam = self.env['hp_components.geo.service'].get_vietnam()
        if not vietnam:
            raise ValidationError('VN does not exists in DB')
        for record in self:
            record.is_local = record.country_id.id == vietnam.id
