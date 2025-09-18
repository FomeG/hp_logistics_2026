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
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        help="Chọn Shipping Line cho Job này"
    )
    vessel = fields.Char(string="Vessel")
    voyage = fields.Char(string="Voyage")
    booking_id = fields.Many2one('freight.purchase.booking', string="Booking")

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
    etd = fields.Datetime(string="ETD")
    eta = fields.Datetime(string="ETA")
    staff_sales = fields.Char(string="Staff Sales")   # thay vì Many2one
    staff_customs = fields.Char(string="Staff Customs")
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
    company_account= fields.Selection(
        selection=lambda self: self._get_bank_selection(),
        string="Company Bank Accounty",
    )
    personal_account = fields.Selection(
        selection=lambda self: self._get_bank_selection(),
        string="Personal Bank Account",
    )
    @api.model
    def create(self, vals):
        if not vals.get('job_number'):
            vals['job_number'] = self.env['ir.sequence'].next_by_code('cs.job.sequence')
        return super(CSJob, self).create(vals)
    def action_print_HBL_bill(self):
        return self.env.ref('hp_customer_service.action_report_HBL_bill').report_action(self)
    def action_print_debit(self):
        return self.env.ref('hp_customer_service.action_report_debit_note').report_action(self)
    def _get_bank_selection(self):
        param = self.env['ir.config_parameter'].sudo().get_param('hp_bank')
        banks = []
        if param:
            try:
                data = json.loads(param)
                for i, bank in enumerate(data):
                    # i bắt đầu từ 0 → trùng với key dict
                    name = f"{bank.get('bank_name')} - {bank.get('bank_account')} ({bank.get('bank_holder_name')})"
                    banks.append((str(i), name))
            except Exception:
                pass
        return banks