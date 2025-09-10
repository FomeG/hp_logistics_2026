from odoo import models, fields, api

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

    @api.model
    def create(self, vals):
        if not vals.get('job_number'):
            vals['job_number'] = self.env['ir.sequence'].next_by_code('cs.job.sequence')
        return super(CSJob, self).create(vals)
