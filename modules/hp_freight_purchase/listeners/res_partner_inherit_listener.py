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
        shipping_line_type = record._get_shipping_line_type()
        shipping_line_contact_type = record._get_shipping_line_contact_type()

        # 1. Nếu partner không có type và không có parent thì gán là shipping_line
        if not record.partner_main_type_id and not record.parent_id and shipping_line_type:
            record.partner_main_type_id = shipping_line_type

        # 2. Nếu partner có parent là shipping_line thì là đó là com và gán shipping_line_contact
        if record.parent_id and record.parent_id.partner_main_type_id == shipping_line_type and shipping_line_contact_type:
            record.partner_main_type_id = shipping_line_contact_type

        # 3. Nếu partner là shipping_line thì cập nhật tất cả con thành shipping_line_contact
        if record.partner_main_type_id == shipping_line_type and shipping_line_contact_type:
            for child in record.child_ids:
                if child.partner_main_type_id != shipping_line_contact_type:
                    child.partner_main_type_id = shipping_line_contact_type
