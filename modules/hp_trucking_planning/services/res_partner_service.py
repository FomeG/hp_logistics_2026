

class ResPartnerService:
    _name = "res.partner.service"

    PARTNER_TYPE_CLIENT = 'client'
    PARTNER_TYPE_DRIVER = 'driver'

    DRIVER_INTERNAL_TYPE = 'internal_driver'
    DRIVER_EXTERNAL_TYPE = 'external_driver'
    
    SHIPPING_LINE = 'shipping_line'

    def __init__(self, env):
        self.env = env
