from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)
class ResPartnerListener(Component):
    _name = "res.partner.listener"
    _inherit = "base.event.listener"
    _apply_on = ['res.partner']

    def on_record_create(self, record, **kwargs):
        record.with_delay().process_set_shipping_line_type()

    # def on_record_write(self, record, **kwargs):
    #     self._set_shipping_line_type(record, kwargs.get("values"))

    def _set_shipping_line_type(self, record, values):
        shipping_line_type = record._get_shipping_line_type()
        shipping_line_contact_type = record._get_shipping_line_contact_type()
        # 1. Nếu partner có parent là shipping_line thì là đó là com và gán shipping_line_contact
        if record.parent_id and not record.partner_main_type_id and record.parent_id.partner_main_type_id == shipping_line_type and shipping_line_contact_type:
            record.partner_main_type_id = shipping_line_contact_type