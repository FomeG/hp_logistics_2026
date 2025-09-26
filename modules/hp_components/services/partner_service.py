from ..models.constants import PartnerMainTypeCode
class PartnerService:
    _name = 'custom_component.partner.service'

    def __init__(self, env):
        self.env = env

    def _get_or_create_partner_main_type_by_code(self, code):
        PartnerMainType = self.env['partner.main.type']
        type = PartnerMainType.search([('code', '=', code)], limit=1)
        if not type:
            type = PartnerMainType.create({
                'name': code,
                'code': code
            })
        return type
    def get_partner_main_type_driver(self):
        return self._get_or_create_partner_main_type_by_code(PartnerMainTypeCode.DRIVER)

    def get_partner_main_type_client(self):
        return self._get_or_create_partner_main_type_by_code(PartnerMainTypeCode.CLIENT)