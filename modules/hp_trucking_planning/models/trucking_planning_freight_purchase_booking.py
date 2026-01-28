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
        RouteModel = self.env['route.base']
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