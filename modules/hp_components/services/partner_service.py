from odoo import models, tools, api
from ..models.constants import PartnerMainTypeCode

class PartnerService(models.AbstractModel):
    _name = 'hp_components.partner.service'
    _description = 'Partner Service'
    
    @tools.ormcache('partner_main_type_code')
    def _get_or_create_partner_main_type_by_code(self, partner_main_type_code):
        PartnerMainType = self.env['partner.main.type']
        type = PartnerMainType.search([('code', '=', partner_main_type_code)], limit=1)
        if not type:
            type = PartnerMainType.create({
                'name': partner_main_type_code,
                'code': partner_main_type_code
            })
        return type

    @api.model
    def get_partner_main_type_driver(self):
        return self._get_or_create_partner_main_type_by_code(PartnerMainTypeCode.DRIVER)

    @api.model
    def get_partner_main_type_client(self):
        return self._get_or_create_partner_main_type_by_code(PartnerMainTypeCode.CLIENT)

    @api.model
    def get_partner_main_type_shipping_line(self):
        return self._get_or_create_partner_main_type_by_code(PartnerMainTypeCode.SHIPPING_LINE)