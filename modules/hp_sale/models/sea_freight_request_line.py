import json
from odoo import models, fields, api
from odoo.addons.hp_components.models.constants import VoyageMode

class SeaFreightRequestLine(models.Model):
    _name = 'freight.purchase.sea.freight.request.line'
    _description = 'Sea Freight Request Line'

    request_id = fields.Many2one(
        comodel_name='freight.purchase.sea.freight.request',
        string="Request",
        required=True,
        ondelete='cascade',
        index=True,
    )
    shipping_line_id = fields.Many2one(
        comodel_name='res.partner',
        string="Carrier",
        domain="[('partner_main_type_id.code', '=', 'shipping_line')]",
        required=True,
        index=True,
    )
    voyage_mode = fields.Selection(
        VoyageMode.SELECT_OPTIONS,
        string="Voyage Mode",
    )
    price = fields.Float(
        string="Price",
        required=True,
    )
    selling_price = fields.Float(
        string="Selling Price",
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id,
    )
    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container Type",
        domain=[('is_active', '=', True)],
    )
    surcharge_ids = fields.Many2many(
        comodel_name='hp.surcharge',
        string="Surcharge",
    )
    free_time = fields.Char(
        string="Free Time",
    )
    etd = fields.Char(
        string="ETD",
        help="JSON array of dates, e.g. [\"2024-01-15\",\"2024-01-20\"]"
    )
    etd_to_add = fields.Date(
        string="Add ETD Date",
        store=False,
    )

    
    etd_display = fields.Html(
        string="ETD Dates",
        compute="_compute_etd_display",
        store=False,
    )
    note = fields.Text(
        string="Note",
    )

    @api.depends('etd')
    def _compute_etd_display(self):
        for record in self:
            if record.etd:
                try:
                    dates = json.loads(record.etd)
                    badges = ''.join(
                        f'<span class="badge rounded-pill text-bg-info me-1">{d}</span>'
                        for d in dates
                    )
                    record.etd_display = badges
                except (json.JSONDecodeError, TypeError):
                    record.etd_display = record.etd
            else:
                record.etd_display = ''

    @api.onchange('price')
    def _onchange_price(self):
        """Automatically fill selling_price with price value"""
        for record in self:
            if record.price:
                record.selling_price = record.price

    @api.onchange('etd_to_add')
    def _onchange_etd_to_add(self):
        """Automatically add selected date to ETD JSON array when date is selected"""
        if not self.etd_to_add:
            return

        date_str = self.etd_to_add.strftime('%Y-%m-%d')

        if self.etd:
            try:
                dates = json.loads(self.etd)
            except (json.JSONDecodeError, TypeError):
                dates = []
        else:
            dates = []

        if date_str not in dates:
            dates.append(date_str)
            dates.sort()

        self.etd = json.dumps(dates)
        self.etd_to_add = False

    # @api.model
    # def _get_etd_dates_selection(self):
    #     """Return current ETD dates as selection options"""
    #     # This is called for selection field - return empty for new records
    #     return []

    # @api.onchange('etd')
    # def _onchange_etd_update_remove_selection(self):
    #     """Update the remove selection options when etd changes"""
    #     if self.etd:
    #         try:
    #             dates = json.loads(self.etd)
    #             return {'domain': {}, 'value': {'etd_to_remove': False}}
    #         except (json.JSONDecodeError, TypeError):
    #             pass
    #     return {}

    # @api.onchange('etd_to_remove')
    # def _onchange_etd_to_remove(self):
    #     """Remove selected date from ETD JSON array"""
    #     if not self.etd_to_remove:
    #         return

    #     date_str = self.etd_to_remove

    #     if self.etd:
    #         try:
    #             dates = json.loads(self.etd)
    #             if date_str in dates:
    #                 dates.remove(date_str)
    #             self.etd = json.dumps(dates) if dates else False
    #         except (json.JSONDecodeError, TypeError):
    #             pass

    #     self.etd_to_remove = False

    # def action_remove_etd(self, date_str):
    #     """Remove a date from ETD JSON array"""
    #     self.ensure_one()
    #     if not self.etd:
    #         return

    #     try:
    #         dates = json.loads(self.etd)
    #         if date_str in dates:
    #             dates.remove(date_str)
    #         self.etd = json.dumps(dates) if dates else False
    #     except (json.JSONDecodeError, TypeError):
    #         pass