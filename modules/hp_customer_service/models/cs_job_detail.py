from odoo import models, fields, api

class CSJobDetail(models.Model):
    _name = 'cs.job.detail'
    _description = 'Job Detail'

    job_id = fields.Many2one('cs.job', string="Job", required=True)
    shipper_id = fields.Many2one('res.partner', string="Shipper", required=True)
    consignee_id = fields.Many2one('res.partner', string="Consignee")
    notify_party_id = fields.Many2one('res.partner', string="Notify Party")
    transport_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')], string="Transport Type")
    freight_charge = fields.Selection([('collect', 'Collect'), ('prepaid', 'Prepaid')], string="Freight & Charge")
    currency_id = fields.Many2one('res.currency', string="Currency")
    status = fields.Selection([('draft','Draft'),('done','Hoàn thành')], string="Status")
    place_of_receipt = fields.Char(string="Place of Receipt")
    place_of_issue = fields.Char(string="Place of Issue")
    prepaid_at = fields.Char(string="Prepaid At")
