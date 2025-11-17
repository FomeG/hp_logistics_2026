# -*- coding: utf-8 -*-
# File: events/cs_order_listener.py

from odoo.addons.component.core import Component
from odoo.addons.hp_components.models import constants


class CsOrderCreateTruckingListener(Component):
    _name = 'cs.order.create_trucking_listener'
    _inherit = 'base.event.listener'
    _apply_on = ['cs.order']

    # def on_record_write(self, record, fields=None):
    #     """Chỉ chạy khi có thay đổi sale_order_id hoặc booking_id"""
    #     if not record.booking_id:
    #         return
    #
    #     trigger_fields = {'sale_order_id', 'booking_id', 'state'}
    #     if fields and not (fields & trigger_fields):
    #         return
    #
    #     # Chỉ tạo khi CS Order đã ở trạng thái In Progress hoặc Done
    #     if record.state not in ['in_progress', 'done']:
    #         return
    #
    #     # Gọi hàm tạo Plan/Job/Trip
    #     record.sudo()._auto_create_trucking_from_cs_order()

    def on_record_create(self, record, fields=None):
        """Khi tạo mới cũng kiểm tra luôn"""
        record.sudo()._auto_create_trucking_from_cs_order()

    def on_record_write(self, record, fields=None):
        if 'booking_id' in fields and record.booking_id:
            record.sudo()._auto_create_trucking_from_cs_order()
