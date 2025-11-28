from odoo import models, fields, api


class IrAttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        help='Booking this document belongs to'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('booking_id'):
                vals.setdefault('res_model', 'freight.purchase.booking')
                vals.setdefault('res_id', vals['booking_id'])
        return super().create(vals_list)

    def _get_department_mapping(self):
        mapping = super()._get_department_mapping()
        mapping.update({
            'freight.purchase.booking': 'Pricing',
        })
        return mapping