from odoo import models, fields, api
from odoo.addons.hp_components.models import constants

class CsOrder(models.Model):
    _name = 'cs.order'
    _inherits = {'project.project': 'project_id'}
    _inherit = ['mail.thread'] # mail activity already have field attachment id so if we add field attachment id in other order it will give error

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True,
    )

    batch_order_id = fields.Many2one(
        comodel_name='cs.batch.order',
        string="Batch Order",
        help="used for monthly billing"
    )
    code = fields.Char(
        string="Cs Ref",
        required=True,
        index=True,
    )
    # Thay thế trường user_id bằng cs_manager_id
    cs_manager_id = fields.Many2one(
        comodel_name='res.users',
        compute='_compute_cs_manager',
        store=True,
        string='CS Manager',
        index=True,
        readonly=True,
    )
    # user_id = fields.Many2one(
    #     comodel_name='res.users',
    #     compute='_compute_cs_manager',
    #     store=True,
    #     string='CS Manager',
    #     index=True,
    #     readonly=True,
    # )

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
    )
    incoterm_id = fields.Many2one(
        comodel_name='account.incoterms',
        string='Incoterm',
        related='sale_order_id.incoterm_id',
        store=True,
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='sale_order_id.booking_id',
    )
    state = fields.Selection(
        constants.CsOrderState.SELECT_OPTIONS,
        string="State",
        default=constants.CsOrderState.DRAFT,
        required=True,
    )
    note = fields.Text()
    delivery_term = fields.Selection(
        constants.DeliveryTerms.SELECT_OPTIONS,
        string="Delivery Term",
        default=constants.DeliveryTerms.CY_CY,
        help=""
            "cy-cy: Delivery from port of departure container yard → port of destination container yard\n"
            "door-cy: Pick up from the shipper's warehouse → deliver to the port of destination container yard\n"
            "cy-door:Delivery from port of departure → to the receiver's warehouse\n"
            "door-door:Delivery from shipper's warehouse → receiver's warehouse",
        required=True,
    )
    service_type = fields.Selection( #service type from sale order is selection
        constants.ServiceType.SELECT_OPTIONS,
        related='sale_order_id.service_type',
        string="Service Type",
        help="Import/Export/Other Service",
        store=False,
    )
    order_name = fields.Char(
        related='sale_order_id.name',
        string='Order Reference',
        index=True,
    )
    salesman_id = fields.Many2one(
        comodel_name='res.users',
        related='sale_order_id.user_id',
        string='Salesman',
        index=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        related='sale_order_id.client_id',
        string='Client',
        index=True,
    )
    commodity = fields.Char(
        related='sale_order_id.commodity',
        store=False,
    )
    commodity_hs_code = fields.Char(
        string="Commodity HS Code",
        related='sale_order_id.commodity_hs_code',
        store=False,
    )

    cs_booking_id = fields.One2many(
        comodel_name="cs.booking",
        inverse_name="cs_order_id",
        string="Booking",
        limit=1
    )
    Booking_code = fields.Char(
        related='cs_booking_id.Booking_code',
        string="Booking Code",
        help="Booking Code",
        index=True,
        store=True,
        readonly=True,
    )
    cs_shipping_instruction_id = fields.One2many(
        comodel_name="cs.shipping.instruction",
        inverse_name="cs_order_id",
        string="Shipping Instruction",
        limit=1
    )
    cs_bill_lading_ids = fields.One2many(
        comodel_name="cs.bill.lading",
        inverse_name="cs_order_id",
        string="BLs",
    )
    cs_pre_alert_id = fields.One2many(
        comodel_name="cs.pre.alert",
        inverse_name="cs_order_id",
        limit=1
    )
    cs_container_ids = fields.One2many(
        comodel_name="cs.container",
        inverse_name="cs_order_id",
        string = "Containers",
    )
    cs_debit_id = fields.One2many(
        comodel_name="cs.debit",
        inverse_name="cs_order_id",
        string = "Debits",
    )
    cs_task_ids = fields.One2many(
        comodel_name="cs.task",
        inverse_name="cs_order_id",
        string = "Tasks",
    )


    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Tự động cập nhật booking_id, name, code khi chọn sale_order_id trong form"""
        if not self.code or not self.name:
            code = self.env['cs.service'].generate_code_from_sale_order(self.sale_order_id, 'cs.order')
            self.code = code
            self.name = code

    @api.depends('sale_order_id', 'sale_order_id.client_id')
    def _compute_cs_manager(self):
        """Tự động lấy leader của department Customer Service"""
        for record in self:
            # Tìm department type CS
            cs_dept_type = self.env['department.type'].search([('code', '=', 'cs')], limit=1)
            cs_department = self.env['hr.department'].search([
                ('department_type_id', '=', cs_dept_type.id)
            ], limit=1) if cs_dept_type else False
            manager_user = cs_department.manager_id.user_id if cs_department and cs_department.manager_id and cs_department.manager_id.user_id else False
            for record in self:
                record.cs_manager_id = manager_user

    @api.model
    def create_from_sale_order(self, sale_order):
        cs_batch_order_id = False
        if sale_order.is_monthly_billing:
            cs_batch_order = self.env['cs.batch.order'].sudo().get_or_create_from_sale_order(sale_order)
            cs_batch_order_id = cs_batch_order.id

        code = self.env['cs.service'].generate_code_from_sale_order(sale_order,'cs.order')
        self.create({
            'name': code, # name is required
            'batch_order_id': cs_batch_order_id,
            'code': code,
            'user_id': self.env.user.id,
            'sale_order_id': sale_order.id,
            'state': constants.CsOrderState.DRAFT,
        })

    def _auto_create_trucking_from_cs_order(self):
        """Tự động tạo Plan → Job → Trip từ CS Order"""
        if not self.booking_id:
            return

        Plan = self.env['trucking_planning.plan']
        PlanLine = self.env['trucking_planning.plan.line']
        Trip = self.env['trucking_planning.trip']

        booking = self.booking_id

        # 1. Tạo Plan
        plan = Plan.search([('booking_bill_no', '=', booking.code)], limit=1)
        if not plan:
            plan_vals = {
                'booking_bill_no': booking.code,
                'plan_type': 'export' if self.service_type == 'export' else 'import',
                # 'location_id': booking.pol_location_id,
                'shipping_line_id': booking.shipping_line_id.id or False,
                'container_type': 'dry',
                'goods_cut_off': booking.etd,
                'status': constants.PlanStatus.DRAFT,
            }
            plan = Plan.sudo().create(plan_vals)
            plan.message_post(body=f"Tự động tạo từ CS Order <a href='#id={self.id}&model=cs.order'>{self.code}</a>")

        # 2. TẠO JOB (Plan Line) từ mỗi Container
        for container in self.cs_container_ids.filtered('container_number'):
            # Kiểm tra trùng (theo container number)
            if PlanLine.search([('plan_id', '=', plan.id), ('code', '=', container.container_number)], limit=1):
                continue

            job_vals = {
                'plan_id': plan.id,
                'code': container.container_number,
                'client_id': self.client_id.id,
                'status': constants.PlanLineStatus.CHECKING,
                # 'route_id': self._get_trucking_route(booking),
                # 'goods_pickup_location_id': booking.pol_id.id,
                # 'goods_delivery_location_id': booking.pod_id.id,
            }
            job = PlanLine.sudo().create(job_vals)

            # 3. TỰ ĐỘNG TẠO TRIP CHO JOB
            Trip.sudo().create({
                'plan_line_id': job.id,
                'container_number': container.container_number,
                'seal_number': container.seal_number or '',
                'container_size': container.container_type_id.name or '40',
                'status': constants.TripStatus.DRAFT,
            })

            job.message_post(body="Đã tự động tạo Trip từ Container")

        # Nếu không có container → tạo 1 Job mặc định
        if not self.cs_container_ids and not plan.plan_line_ids:
            job = PlanLine.sudo().create({
                'plan_id': plan.id,
                'code': f"AUTO-{self.code}",
                'client_id': self.client_id.id,
                'status': constants.PlanLineStatus.CHECKING,
            })
            Trip.sudo().create({'plan_line_id': job.id, 'status': constants.TripStatus.DRAFT})

    # Helper methods
    # def _get_trucking_route(self, booking):
    #     route = self.env['trucking_planning.route'].search([
    #         ('from_location_id', '=', booking.pol_id.id),
    #         ('to_location_id', '=', booking.pod_id.id)
    #     ], limit=1)
    #     return route.id if route else False
