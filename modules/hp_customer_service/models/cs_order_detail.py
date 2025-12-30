from odoo import models, fields, api


class CsOrderDetail(models.AbstractModel):
    _name = 'cs.order.detail'
    _inherits = {'project.task': 'task_id'}
    _description = 'CS Order Detail'

    task_id = fields.Many2one(
        comodel_name="project.task",
        required=True,
        ondelete="cascade"
    )

    cs_order_id = fields.Many2one(
        string='CS Order',
        comodel_name='cs.order',
        index=True,
        ondelete='cascade',
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='cs_order_id.booking_id',
        string="Booking",
    )


    @api.model_create_multi
    def create(self, vals_list):

        cs_order_ids = {v['cs_order_id'] for v in vals_list if v.get('cs_order_id')}
        cs_orders = self.env['cs.order'].browse(list(cs_order_ids))
        cs_order_map = {o.id: o for o in cs_orders}
        
        # Map tạm để lưu sale_order_id dự định gán cho từng index
        # Key: index trong vals_list, Value: sale_order_id
        pending_sale_orders = {} 

        model_desc = self._description or 'CS Order Detail'

        for idx, vals in enumerate(vals_list):
            cs_order = cs_order_map.get(vals.get('cs_order_id'))
            if not cs_order:
                continue

            if cs_order.project_id and 'project_id' not in vals:
                vals['project_id'] = cs_order.project_id.id
            
            # Lưu lại ID cần update để xử lý sau (để tránh bị super() loại bỏ)
            if cs_order.sale_order_id:
                pending_sale_orders[idx] = cs_order.sale_order_id.id

            if 'name' not in vals:
                source_name = cs_order.code or cs_order.name or ''
                vals['name'] = f"{model_desc} - {source_name}"

        # 2. Tạo record
        records = super().create(vals_list)

        # 3. Batch Update (Tránh N+1 Write)
        updates = {}
        
        for idx, record in enumerate(records):
            so_id = pending_sale_orders.get(idx)
            if so_id:
                if so_id not in updates:
                    updates[so_id] = record
                else:
                    updates[so_id] |= record # Gom recordset (union)

        # Thực hiện Update (Số lượng query = Số lượng Sale Order khác nhau)
        # Nếu 1000 records nhưng chỉ thuộc về 2 Sale Order -> Chỉ tốn 2 query update.
        for so_id, recs in updates.items():
            # Write thẳng vào task_id để đảm bảo hiệu suất
            recs.mapped('task_id').write({'sale_order_id': so_id})

        return records






    # @api.model_create_multi
    # def create(self, vals_list):
    #     # Collect sale_order data for post-create update
    #     sale_order_map = {}

    #     for idx, vals in enumerate(vals_list):
    #         cs_order_id = vals.get('cs_order_id')
    #         if not cs_order_id:
    #             continue

    #         cs_order = self.env['cs.order'].browse(cs_order_id)
    #         if not cs_order.exists():
    #             continue

    #         if cs_order.project_id and 'project_id' not in vals:
    #             vals['project_id'] = cs_order.project_id.id

    #         if cs_order.sale_order_id:
    #             sale_order_map[idx] = cs_order.sale_order_id.id

    #         if 'name' not in vals:
    #             model_desc = self._description or 'CS Order Detail . . .'
    #             source_name = cs_order.code or cs_order.name or ''
    #             vals['name'] = f"{model_desc} - {source_name}"

    #     records = super().create(vals_list)

    #     for idx, record in enumerate(records):
    #         sale_order_id = sale_order_map.get(idx)
    #         if sale_order_id and record.task_id:
    #             record.task_id.sale_order_id = sale_order_id

    #     return records