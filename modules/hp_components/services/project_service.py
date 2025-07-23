
class ProjectService:
    _name = 'project.service'

    PROJECT_TYPE_PRICE_REQUEST = 'request_price'
    PROJECT_TYPE_APPROVE_QUOTATION = 'approve_quotation'
    PROJECT_TYPE_PRODUCT_REQUEST = 'request_product'
    PROJECT_TYPE_ASSIGN_BOOKING = 'assign_booking'

    ACTION_APPROVE_POL_POL = 'approve_pod_pol'
    ACTION_APPROVE_PRICE = 'approve_price'
    ACTION_ASSIGN_BOOKING = 'assign_booking'
    ACTION_REJECT_QUOTATION_BY_PRICING = 'reject_quotation_by_pricing'
    ACTION_REJECT_QUOTATION_BY_SALE = 'reject_quotation_by_sale'
    ACTION_APPROVE_QUOTATION_BY_PRICING = 'approve_quotation_by_pricing'
    ACTION_APPROVE_QUOTATION_BY_SALE = 'approve_quotation_by_sale'

    def __init__(self, env):
        self.env = env

    def get_project_by_type(self, project_type=''):
        project = self.env['project.project'].search([('type', '=', project_type)], limit=1)
        return project if project else False
    