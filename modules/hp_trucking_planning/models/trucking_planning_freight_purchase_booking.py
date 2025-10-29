from .plan import Plan
from .plan_line import PlanLine
from odoo import models, api, fields
from datetime import datetime
from odoo.addons.hp_components.models import constants
import logging

_logger = logging.getLogger(__name__)

class TruckingPlanningFreightPurchaseBooking(models.Model):
    _name = 'trucking_planning.freight.purchase.booking'
    _inherits = {'freight.purchase.booking':'booking_id'}

    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        string='Booking',
        required=True,
        ondelete='cascade',
        index=True,
    )
    def _get_or_create_freight_route_from_demo(self):
        RouteModel = self.env['freight.purchase.route']
        pol_id = 1 #from demo data
        pod_id = 4 #from demo data
        route = RouteModel.search([('pol_id', '=', pol_id),('pod_id', '=', pod_id)])
        if not route:
            route = RouteModel.create({
                'pol_id': pol_id,
                'pod_id': pod_id,
                'is_active': True, #todo remove this from validatior as it can use the default value
            })
        return route
    @api.model
    def create_booking_from_plan(self, record: Plan):

        existing_booking = self.search([
            ('code', '=', record.booking_bill_no)
        ], limit=1)

        if existing_booking:
            _logger.info(f"Booking already exists for {record.booking_bill_no}, skip auto-creation.")
            return
        route = self._get_or_create_freight_route_from_demo()
        if not route:
            _logger.error(f"No route found in purchase data")
            return

        booking_vals = {
            'booking_mode': constants.BookingMode.WITHOUT_QUOTATION,
            'code': record.booking_bill_no,
            'vessel_id': 1, #from demo data
            'status': constants.BookingStatus.CONFIRMED,
            'note': f"Auto-created from Trucking Plan {record.name}",
            'quotation_shipping_line_id': record.shipping_line_id.id,
            'quotation_route_id': route.id,
            'etd': datetime.now().strftime("%Y-%m-%d"),
        }
        booking = super(TruckingPlanningFreightPurchaseBooking,self).create(booking_vals)
        record.write({'booking_id': booking.booking_id})
        _logger.info(f"[Plan→Booking] Created booking {booking.name} for plan {record.name}")