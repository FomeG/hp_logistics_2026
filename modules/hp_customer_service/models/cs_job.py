from odoo import models, fields, api
import base64, os
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
    job_number_reference = fields.Char(
        string="Job Number Reference",
    )
    department = fields.Char(string="Department", default="SEA EXPORT")
    master_bl_date = fields.Char(string="Master B/L Date")
    shipping_lines = fields.Char(string="Shipping Lines")  # thay vì Many2one
    vessel = fields.Char(string="Vessel")
    voyage = fields.Char(string="Voyage")
    port_loading = fields.Char(string="Port of Loading")   # thay vì Many2one
    port_discharge = fields.Char(string="Port of Discharge")
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
    @api.model
    def create(self, vals):
        if not vals.get('job_number'):
            vals['job_number'] = self.env['ir.sequence'].next_by_code('cs.job.sequence')
        return super(CSJob, self).create(vals)
    def action_print_HBL_bill(self):
        return self.env.ref('hp_customer_service.action_report_HBL_bill').report_action(self)
    def action_print_debit(self):
        return self.env.ref('hp_customer_service.action_report_debit_note').report_action(self)
    def _get_report_values(self, docids, data=None):
        docs = self.env['cs.job'].browse(docids)

        # Lấy logo từ static module
        module_path = os.path.dirname(__file__)
        logo_path = os.path.join(module_path, '..', 'static', 'src', 'img', 'logo.png')
        logo_base64 = ''
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_base64 = base64.b64encode(f.read()).decode('utf-8')

        return {
            'docs': docs,
            'logo_base64': logo_base64,
        }