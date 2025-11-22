from odoo import models, fields, api
from ..services.vehicle_service import VehicleService
from ..services.res_partner_service import ResPartnerService
import re
from odoo.addons.hp_components.models import constants
from odoo.addons.hp_components.services import partner_service

from ...hp_components.services.partner_service import PartnerService


class FleetVehicleInherit(models.Model):
    _inherit = ['fleet.vehicle']

    driver_id = fields.Many2one(
        domain=lambda self:self._get_driver_domain()
    )

    # will be replaced by "fleet.vehicle.assignation.log"
    vehicle_assignment_log_ids = fields.One2many(
        comodel_name='fleet.vehicle.assignation.log',
        inverse_name='vehicle_id',
    )
    trucking_branch_id = fields.Many2one(
        comodel_name='trucking_planning.branch',
        index=True,
        default=lambda self: self._get_default_branch(),
    )
    _sql_constraints = [
        ('unique_license_plate', 'unique(license_plate)', 'This license_plate is already assigned to another vehicle.'),
    ]

    @api.model
    def _get_default_branch(self):
        return self.env['trucking_planning.branch'].sudo().search([('user_ids', 'in', [self.env.uid])], limit=1)

    @api.model
    def _get_driver_domain(self):
        return [(
            'partner_main_type_id','=',self.env['hp_components.partner.service'].get_partner_main_type_driver().id
        )]