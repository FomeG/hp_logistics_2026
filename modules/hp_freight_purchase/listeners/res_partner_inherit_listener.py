from odoo.addons.component.core import Component
import logging

_logger = logging.getLogger(__name__)
class ResPartnerListener(Component):
    _name = "res.partner.listener"
    _inherit = "base.event.listener"
    _apply_on = ['res.partner']

    def on_record_create(self, record, **kwargs):
        self._set_shipping_line_type(record, kwargs.get("values"))

    def on_record_write(self, record, **kwargs):
        self._set_shipping_line_type(record, kwargs.get("values"))

    def _set_shipping_line_type(self, record, values):
        if values is None:
            values = {}

        shipping_line_type = record._get_shipping_line_type()
        shipping_line_contact_type = record._get_shipping_line_contact_type()

        if not record.partner_main_type_id and not record.parent_id and shipping_line_type:
            record.partner_main_type_id = shipping_line_type

        if record.parent_id and record.parent_id.partner_main_type_id == shipping_line_type and shipping_line_contact_type:
            record.partner_main_type_id = shipping_line_contact_type