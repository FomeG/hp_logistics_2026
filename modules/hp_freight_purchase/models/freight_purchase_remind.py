from odoo import models, fields, api
from odoo.exceptions import ValidationError

class FreightPurchaseRemind(models.Model):
    _name = 'freight.purchase.remind'
    _description = 'Reminder Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin','unique.normalized.name.mixin']

    total = fields.Integer(string='Total Reminders', default=3, required=True)
    interval = fields.Float(string='Interval (Hours)', default=1.0, required=True, help="Time between reminders, in hours.")
    type = fields.Selection(
        string="Type",
        selection=[
            ('booking_line', f"Booking Line"),
        ],
        default='booking_line',
        store=True,
    )
    is_active = fields.Boolean(string='Is Active', default=True, tracking=True)

    without_booking_line_ids = fields.One2many('freight.purchase.booking.line', 'remind_id', string='Booking Lines')

    @api.constrains('type', 'is_active')
    def _check_unique_active_type(self):
        for record in self:
            if record.is_active and record.type:
                domain = [
                    ('type', '=', record.type),
                    ('is_active', '=', True),
                    ('id', '!=', record.id)
                ]
                duplicate = self.search(domain, limit=1)
                if duplicate:
                    raise ValidationError(
                        f"Only one active reminder configuration is allowed for type '{record.type}'."
                    )