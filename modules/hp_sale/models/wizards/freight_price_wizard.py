from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
from odoo.addons.hp_components.models.constants import TransportMode

_logger = logging.getLogger(__name__)
class GetFreightPriceWizard(models.TransientModel):

    _name = 'hp_sale.freight.price.wizard'
    _description = 'Freight Price Wizard'

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        limit =1
    )
    line_ids = fields.One2many(
        comodel_name='hp_sale.freight.price.wizard.line',
        inverse_name='wizard_id'
    )
    can_request_price = fields.Boolean(
        default=False,
    )
    can_add_item = fields.Boolean(
        default=False,
    )
    def _validate_params(self,sale_order_id):
        so = False
        if not sale_order_id:
            _logger.error('Sale Order ID is required')
            raise ValidationError("Sale Order is required")
        else:
            so = self.env['sale.order'].browse(sale_order_id)
            if not so:
                _logger.error('Invalid Sale Order ID: %s', sale_order_id)
                raise ValidationError("Sale Order is invalid")
        return so

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        so_id = self.env.context.get('default_sale_order_id')
        so = self._validate_params(so_id)
        freight_prices = self.env['hp_sale.sale.service'].get_freight_price_by_sale_order(so)
        line_ids = []
        # Process SEA freight (if exists)
        sea_data = freight_prices.get('sea', {})
        if sea_data:
            primary_data = sea_data.get('primary', False)
            suggestion_data = sea_data.get('suggestion', False)
            if primary_data:
                self._build_wizard_lines(line_ids, primary_data, TransportMode.SEA, sea_data['from_id'],sea_data['to_id'])
            if suggestion_data:
                self._build_wizard_lines(line_ids, suggestion_data, TransportMode.SEA, sea_data['from_id'],sea_data['to_id'], True)

        # Process TRUCK freight (always exists based on your logic)
        truck_data = freight_prices.get('truck', {})
        if truck_data:
            self._build_wizard_lines(line_ids, truck_data.get('price_data', []),TransportMode.TRUCK, truck_data['from_id'],truck_data['to_id'])

        res['line_ids'] = line_ids
        res['sale_order_id'] = so_id
        for line in line_ids:
            if line[2].get('price') == 0:
                res['can_request_price'] = True
            else:
                res['can_add_item'] = True

        return res

    def action_add_to_order(self):
        self.ensure_one()
        if not self.can_add_item:
            raise ValidationError("Can't add item")

        so = self.sale_order_id
        sea_freight_product_id = self.env.ref('hp_sale.product_sea_freight')
        truck_freight_product_id = self.env.ref('hp_sale.product_truck_freight')
        lines = self.env['hp_sale.freight.price.wizard.line'].search([
            ('wizard_id', '=', self.id),
            ('selected', '=', True),
        ])
        for line in lines:
            product_id = truck_freight_product_id
            if line.transport_mode == TransportMode.SEA:
                product_id = sea_freight_product_id

            src = line.source_ref  # record thực
            model_name = src._name
            record_id = src.id
            # Lấy ir.model tương ứng
            model_rec = self.env['ir.model']._get(model_name)

            so.order_line.create({
                'order_id': so.id,
                'name': line.name,
                'price_unit': line.price,
                'product_id': product_id.product_variant_id.id,
                'res_model_id': model_rec.id,
                'res_id': record_id,
            })

        return {'type': 'ir.actions.act_window_close'}

    def _build_wizard_lines(self,lines, freight_prices, transport_mode, from_location_id, to_location_id, suggestion = False):
        for freight_price in freight_prices:
            source_ref = False
            price = freight_price.get('price', 0)
            if freight_price.get('model') and freight_price.get('model_id'):
                source_ref = f"{freight_price.get('model')},{freight_price.get('model_id')}"
            lines.append((0, 0, {
                'transport_mode': transport_mode,
                'source_ref': source_ref,
                'from_location_id': from_location_id,
                'to_location_id': to_location_id,
                'shipping_line_id': freight_price.get('shipping_line_id', False),
                'container_type_id': freight_price.get('container_type_id', False),
                'price': price,
                'currency_id': freight_price.get('currency_id', self.env.company.currency_id.id),
                'suggestion':suggestion
            }))

    def action_request_price(self):
        self.ensure_one()
        _logger.info(f"Request price for {self.id}")
