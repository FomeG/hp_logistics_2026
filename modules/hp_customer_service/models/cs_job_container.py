from odoo import models, fields, api

class CSJobContainer(models.Model):
    _name = 'cs.job.container'
    _description = 'Container Detail'

    job_id = fields.Many2one('cs.job', string="Job", required=True, ondelete='cascade')
    container_number = fields.Char(string="Container No")
    container_type_id = fields.Many2one('container.type', string="Container Type")
    seal_number = fields.Char(string="Seal No")
    gross_weight = fields.Float(string="Gross Weight (KG)")
    net_weight = fields.Float(string="Net Weight (KG)")
    description = fields.Char(string="description")

    package_type = fields.Char(string="Package Type")  # or Many2one if có bảng riêng
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    volume_cbm = fields.Float(string="Volume (CBM)")

    # Pickup info
    pickup_instruction = fields.Text(string="Pickup Instruction")
    pickup_address = fields.Char(string="Pickup Address")
    pickup_date = fields.Date(string="Pickup Date")
    status = fields.Selection([
        ('pending', 'Pending'),
        ('stuffing', 'Stuffing'),
        ('loaded', 'Loaded'),
        ('completed', 'Completed'),
    ], default='pending', string="Status")
    booking_line_id = fields.Many2one(
        'freight.purchase.booking.line',
        related='job_id.booking_line_id',
        store=True
    )

