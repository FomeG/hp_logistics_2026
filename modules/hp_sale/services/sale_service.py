from odoo import models, api
import logging

_logger = logging.getLogger(__name__)
class SaleService(models.AbstractModel):
    _name = 'hp_sale.sale.service'
    _description = 'Sale Service'

    def get_freight_price_by_sale_order(self, sale_order):
        result = {}
        if sale_order.is_sea_exp_location:
            goods_location_id = sale_order.goods_location_id.id
            local_port_location_id = sale_order.from_location_id.id
            to_port_location_id = sale_order.to_location_id.id
            truck_freight_price = self.get_truck_freight_price(
                from_location_id=goods_location_id,
                to_location_id=local_port_location_id
            )
            result['truck'] = {
                'from_id': goods_location_id,
                'to_id': local_port_location_id,
                'price_data': truck_freight_price
            }
            sea_freight_prices = self.get_sea_freight_price(
                etd=sale_order.etd,
                from_location_id=local_port_location_id,
                to_location_id=to_port_location_id,
                shipping_line_id=sale_order.shipping_line_id.id if sale_order.shipping_line_id else None,
                container_type_id=sale_order.container_type_id.id if sale_order.container_type_id else None,
            )
            result['sea'] = {
                'from_id': local_port_location_id,
                'to_id': to_port_location_id,
                'primary':sea_freight_prices.get('primary', False),
                'suggestion': sea_freight_prices.get('suggestion', False),
            }
        else:
            from_location_id = sale_order.goods_location_id.id
            to_location_id = sale_order.to_location_id.id
            truck_freight_price = self.get_truck_freight_price(
                from_location_id =from_location_id,
                to_location_id = to_location_id
            )
            result['truck'] = {
                'from_id': from_location_id,
                'to_id': to_location_id,
                'price_data': truck_freight_price
            }
            result['sea'] = {}

        return result

    def get_sea_freight_price(self, etd=None, from_location_id=None, to_location_id=None,
                              shipping_line_id=None, container_type_id=None):
        result_no_price = {
            'primary': [
                {
                    'price': 0,
                    'shipping_line_id': shipping_line_id,
                    'container_type_id': container_type_id,
                }
            ]
        }
        if not etd:
            return result_no_price
        # need at least 1 selling week around this etd
        selling_week = self.env['selling.week'].search_read([
            '|',
            '&', ('start_date', '<=', etd), ('end_date', '>=', etd),
            ('start_date', '>', etd),
        ], ['id', 'start_date'], order='start_date asc', limit=1)

        if not selling_week:
            return result_no_price
        selling_week_id = selling_week[0]['id']

        #check if the trip (from - to) has selling price in this period
        #be sure to get right record that is belongs to team region
        trip_per_team_domain = [
            ('selling_week_id', '=', selling_week_id),
            ('from_location_id', '=', from_location_id),
            ('to_location_id', '=', to_location_id),
        ]
        selling_price_trip_team = self.env['product.template.selling.week'].search_read(trip_per_team_domain, ['id'], limit=1)

        if not selling_price_trip_team:
            return result_no_price

        sellingPriceModel = self.env['product.template.selling.week.line']
        selling_price_trip_team_id = selling_price_trip_team[0]['id']
        user_request_domain = [
            ('product_template_selling_week_id', '=', selling_price_trip_team_id)
        ]
        if shipping_line_id:
            user_request_domain.append(('shipping_line_id', '=', shipping_line_id))

        if container_type_id:
            user_request_domain.append(('container_type_id', '=', container_type_id))

        scenarios_domains = []
        #specifik shipping line and container
        if shipping_line_id and container_type_id:
            scenarios_domains.append([
                ('product_template_selling_week_id', '=', selling_price_trip_team_id),
                ('shipping_line_id', '=', shipping_line_id),
                ('container_type_id','=', container_type_id)
            ])
        #specifik only shipping line
        scenarios_domains.append([
            ('product_template_selling_week_id', '=', selling_price_trip_team_id),
            ('shipping_line_id','=',shipping_line_id)
        ])
        #specifik only container
        scenarios_domains.append([
            ('product_template_selling_week_id', '=', selling_price_trip_team_id),
            ('container_type_id', '=', container_type_id)
        ])
        #accept all
        scenarios_domains.append([
            ('product_template_selling_week_id', '=', selling_price_trip_team_id),
        ])
        primary_result = []
        suggestion_result = []
        for scenario in scenarios_domains:
            is_user_request = False
            if scenario == user_request_domain:
                is_user_request = True
            selling_prices = sellingPriceModel.search(
                scenario,
            )
            result = []
            if selling_prices:
                for selling_price in selling_prices:
                    result.append({
                        'model': 'product.template.selling.week.line',
                        'model_id': selling_price.id,
                        'shipping_line_id': selling_price.shipping_line_id.id,
                        'container_type_id': selling_price.container_type_id.id,
                        'price': selling_price.price,
                        'currency_id': selling_price.currency_id
                    })
                # need only 1 result
                if is_user_request:
                    primary_result = result
                else:
                    suggestion_result = result
                break
            #need to keep primary result in case not found
            elif is_user_request:
                primary_result = [
                    {
                        'price': 0,
                        'shipping_line_id': shipping_line_id,
                        'container_type_id': container_type_id,
                    }]
        return {
            'primary': primary_result,
            'suggestion': suggestion_result,
        }

    @api.model
    def get_truck_freight_price(self, from_location_id=None, to_location_id=None):
        locationBaseModel = self.env['location.base']
        from_location = locationBaseModel.browse(from_location_id)
        to_location = locationBaseModel.browse(to_location_id)
        route = self.env['hp_components.geo.service'].get_route_between_locations(
            from_location, to_location
        )
        price = 0
        if route:
            price = route.total_cost
        return [
            {
                'model': 'route.base',
                'model_id': route.id,
                'price': price,
                'currency_id': self.env.ref('base.VND').id,
            }
        ]