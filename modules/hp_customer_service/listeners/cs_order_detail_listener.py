from odoo.addons.component.core import Component


class CsOrderDetailListener(Component):
    _name = 'cs.order.detail.listener'
    _inherit = 'base.event.listener'
    _apply_on = [
        'cs.booking',
        'cs.container',
        'cs.debit',
        'cs.shipping.instruction',
        'cs.shipping.document',
        'cs.pre.alert',
        'cs.bill.lading',
    ]



    def on_record_create(self, record, fields=None):
        # khi các model cs item được tạo -> tao luôn cs.task liên quan
        if not record.cs_order_id:
            return

        task = self._create_cs_task(record)
        if task:
            # Use SQL to avoid triggering on_record_write event
            self.env.cr.execute(
                "UPDATE %s SET cs_task_id = %%s WHERE id = %%s" % record._table,
                (task.id, record.id)
            )
            record.invalidate_recordset(['cs_task_id'])



            

    def _create_cs_task(self, record):
        """Create cs.task for the given cs.order.detail record"""
        cs_order = record.cs_order_id

        if not cs_order.project_id:
            return False

        # Create cs.task - project_id and sale_order_id are set in cs.task.create()
        task = self.env['cs.task'].with_context(__no_event=True).create({
            'name': record._description or record._name,
            'cs_order_id': cs_order.id,
        })

        return task
