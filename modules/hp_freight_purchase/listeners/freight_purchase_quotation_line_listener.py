from odoo.addons.component.core import Component
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class FreightPurchaseQuotationListener(Component):
    _name = 'freight.purchase.quotation.line.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['freight.purchase.quotation.line']

    # def on_record_create(self, record, fields=None):
    #     record._auto_create_product_selling_week()
        

