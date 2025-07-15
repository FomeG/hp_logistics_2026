from odoo import models, fields, api


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        help='Booking this document belongs to'
    )
    document_type = fields.Selection([
        ('booking_file', 'Booking File'),
        ('bl_draft', 'B/L Draft'),
        ('bl_final', 'B/L Final'),
        ('invoice', 'Invoice'),
        ('co', 'Certificate of Origin'),
        ('other', 'Other')
    ], string='Document Type')
    department = fields.Many2one(comodel_name='hp.department',string="Department")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_id'):
                vals.setdefault('res_model', 'freight.purchase.booking')
                vals.setdefault('res_id', vals['booking_id'])
        return super().create(vals_list)

