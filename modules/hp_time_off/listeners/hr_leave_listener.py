from odoo.addons.component.core import Component

import logging
_logger = logging.getLogger(__name__)

class HrLeaveListener(Component):
    _name = 'hr.leave.listener'
    _inherit = 'base.event.listener'
    _apply_on = ['hr.leave']


    def on_record_write(self, record, fields=None):
        if 'state' in fields:
            record.with_delay()._handle_record_write()

            if record.state == 'refuse':
                record.sudo().write({
                    'request_refuse': False,
                })

        return 