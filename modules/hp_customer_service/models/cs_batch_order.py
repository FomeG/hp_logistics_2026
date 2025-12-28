from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta

class CsBatchOrder(models.Model):
    _name = 'cs.batch.order'
    _description = 'Cs Batch Order'

    name = fields.Char(
        required=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        required=True,
        index=True,
    )

    cs_order_ids = fields.One2many(
        comodel_name='cs.order',
        inverse_name='batch_order_id',
    )

    @api.model
    def get_or_create_from_sale_order(self, sale_order):
        today = date.today()
        first_day_of_month = date(today.year, today.month, 1)
        last_day_of_month = first_day_of_month + relativedelta(months=1, days=-1)
        current_batch = self.search([
            ('client_id', '=', sale_order.client_id.id),
            ('create_date', '>=', first_day_of_month.strftime('%Y-%m-%d')),
            ('create_date', '<=', last_day_of_month.strftime('%Y-%m-%d'))
        ], limit=1)
        if not current_batch:
            name = self.env['cs.service'].generate_code_from_sale_order(sale_order,'cs.batch.order')
            current_batch = self.create({
                'name': name,
                'client_id': sale_order.client_id.id,
            })

        return current_batch
