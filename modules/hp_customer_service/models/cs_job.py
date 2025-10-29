from odoo import models, fields, api
import base64, os, json
class CSJob(models.Model):
    _name = 'cs.job'
    _description = 'Customer Service Job Information'
    _rec_name = 'job_number'
    job_number = fields.Char(
        string="Job Number",
        required=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('cs.job.sequence')
    )
    job_date = fields.Date(string="Job Date", required=True, default=fields.Date.today)
    service_type = fields.Selection(
        [('door-cy', 'Door to CY'), ('cy-cy', 'CY to CY')],
        string="Service Type",
        default='door-cy'
    )
    department_code = fields.Selection(
        selection=[
            ('JP01', 'SEA EXPORT'),
            ('JP02', 'SEA IMPORT'),
            ('JP03', 'AIR EXPORT'),
            ('JP04', 'AIR IMPORT'),
            ('JP05', 'LAND'),
            ('JP06', 'MISCELLANEOUS'),
            ('JP07', 'SALES AND MARKETING'),
            ('JP08', 'ADMINISTRATION'),
        ],
        string="Department",
        required=True,
    )
    master_bl_date = fields.Char(string="Master B/L Date")
    shipping_line_id = fields.Many2one(
        'res.partner',
        string="Shipping Line",
        related='booking_id.shipping_line_id'
    )
    container_ids = fields.One2many(
        'cs.job.container',
        'job_id',
        string="Shipping Line",
    )
    vessel_transit = fields.Many2one(
        'freight.purchase.vessel',
        string="Vessel transit",
    )
    vessel = fields.Many2one(
        'freight.purchase.vessel',
        string="Vessel",
        related="booking_id.vessel_id",
        store=True,
        readonly=True,
    )
    voyage = fields.Char(string="Voyage",related="booking_id.quotation_id.code",)
    booking_id = fields.Many2one('freight.purchase.booking', string="Booking")
    booking_line_id = fields.Many2one(
        'freight.purchase.booking.line',
        string="Booking Line (Customer)",
        domain="[('booking_id', '=', booking_id)]",  # lọc chỉ các line thuộc booking đang chọn
        # required=True
    )

    port_loading = fields.Many2one(
        'freight.purchase.port',
        string="Port of Loading",
        related = 'booking_id.pol_id'
    )

    port_discharge = fields.Many2one(
        'freight.purchase.port',
        string="Port of Discharge",
        related='booking_id.pod_id'

    )
    quantity = fields.Integer(
        string="Numbers of Container",
        related = 'booking_line_id.quantity'
    )
    container_type_id = fields.Many2one(
        'container.type',
        string="Container Type",
        related='booking_line_id.container_type_id',
        store=True
    )
    container_summary = fields.Char(string="Numbers of Container", compute="_compute_container_summary")

    port_transit = fields.Char(string="Port of Transit")
    pre_carriage_by = fields.Char(string="Pre-Carriage By")
    commodity = fields.Char(string="Commodity")
    booking_number = fields.Char(string="Booking Number")
    booking_party = fields.Char(string="Booking Party")
    bill_type = fields.Selection(
        [('hbl', 'House B/L'), ('mbl', 'Master B/L')],
        string="Bill Type",
        default='hbl'
    )
    etd = fields.Date(related="booking_id.etd", store=True)
    mother_etd = fields.Date(string="Mother Vessel ETD")
    eta = fields.Datetime(string="ETA")
    customer_id = fields.Many2one('res.partner', related='booking_line_id.customer_id', string='Customer')
    salesman_id = fields.Many2one('res.users', related='booking_line_id.salesman_id', string='Salesperson')

    date_of_master_bl_date = fields.Char(string="date of master bl date")
    detail_ids = fields.One2many(
        'cs.job.detail',  # model chứa chi tiết
        'job_id',  # field Many2one trỏ về cs.job
        string="Job Details"
    )
    carrier = fields.Char(string="carrier")
    port_delivery = fields.Char(string="port_delivery")
    port_receipt =  fields.Char(string="port_receipt")
    pre_carriage_vessel = fields.Char(string="Pre-Carriage Vessel")
    pre_carriage_voy = fields.Char(string="Pre-Carriage Voyage")
    mbl_number = fields.Char(string="Master B/L Number")
    hbl_number = fields.Char(string="House B/L Number")

    stuffed_containers = fields.Integer(
        string="Stuffed Containers",
        compute="_compute_container_progress",
        store=False
    )

    total_containers = fields.Integer(
        string="Total Containers",
        compute="_compute_container_progress",
        store=False
    )

    container_progress = fields.Char(
        string="Container Progress",
        compute="_compute_container_progress",
        store=False
    )

    _sql_constraints = [
        ('unique_job_number', 'unique(job_number)', 'The job_number must be unique.')
    ]

    @api.depends('container_ids', 'container_ids.status', 'booking_line_id.quantity')
    def _compute_container_progress(self):
        for job in self:
            total_planned = job.booking_line_id.quantity or 0

            # Lấy tất cả Job khác dùng cùng Booking Line
            related_jobs = self.env['cs.job'].search([
                ('booking_line_id', '=', job.booking_line_id.id)
            ])

            # Đếm container đã có trong tất cả job liên quan
            stuffed = sum(len(j.container_ids.filtered(
                lambda c: c.status in ['stuffing', 'loaded', 'completed']
            )) for j in related_jobs)

            job.stuffed_containers = stuffed
            job.total_containers = total_planned
            job.container_progress = f"{stuffed}/{total_planned}"

    # company_account= fields.Selection(
    #     selection=lambda self: self._get_bank_selection('company'),
    #     string="Company Bank Account",
    # )
    # personal_account = fields.Selection(
    #     selection=lambda self: self._get_bank_selection('personal'),
    #     string="Personal Bank Account",
    # )
    @api.depends('quantity', 'container_type_id')
    def _compute_container_summary(self):
        for rec in self:
            if rec.quantity and rec.container_type_id:
                rec.container_summary = f"{rec.quantity} x {rec.container_type_id.name}"
            else:
                rec.container_summary = "-"
    @api.onchange('booking_id')
    def _onchange_booking_id(self):
        if self.booking_id:
            self.port_transit = self.booking_id.route_transit_id.name or ''

    @api.model
    def create(self, vals):
        if not vals.get('job_number'):
            vals['job_number'] = self.env['ir.sequence'].next_by_code('cs.job.sequence')
        return super(CSJob, self).create(vals)
    def action_print_HBL_bill(self):
        return self.env.ref('hp_customer_service.action_report_HBL_bill').report_action(self)
    def action_print_debit(self):
        return self.env.ref('hp_customer_service.action_report_debit_note').report_action(self)
    # def _get_bank_selection(self, bank_type=None):
    #     param = self.env['ir.config_parameter'].sudo().get_param('hp_bank')
    #     banks = []
    #     if param:
    #         try:
    #             data = json.loads(param)
    #             for i, bank in enumerate(data):
    #                 # lọc theo type + active
    #                 if bank.get('type') == bank_type and bank.get('active', True):
    #                     name = f"{bank.get('bank_name')} - {bank.get('bank_account')} ({bank.get('bank_holder_name')})"
    #                     banks.append((str(i), name))
    #         except Exception:
    #             pass
    #     return banks
    @api.onchange('booking_line_id')
    def _onchange_booking_line_id_generate_containers(self):
        if self.booking_line_id:
            # Xóa container cũ nếu muốn reset
            self.container_ids = [(5, 0, 0)]

            # Lấy số lượng container của Booking Line
            total_qty = self.booking_line_id.quantity or 0
            container_type = self.booking_line_id.container_type_id

            # Tạo các container line tự động
            containers = []
            for i in range(total_qty):
                containers.append((0, 0, {
                    'container_type_id': container_type.id,
                    'status': 'pending',
                }))
            self.container_ids = containers
