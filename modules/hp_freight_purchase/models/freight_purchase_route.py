from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.addons.hp_components.models import constants

class FreightPurchaseRoute(models.Model):

    _inherit = ['route.base']
    _description = 'Route'
    _order = 'create_date desc'

    pol_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        tracking=True,
        ondelete='cascade',
        compute='_compute_pol_pod',
    )
    pod_id = fields.Many2one(
        comodel_name='location.base',
        required=True,
        tracking=True,
        ondelete='cascade',
        compute='_compute_pol_pod',
    )

    quotation_ids = fields.One2many(
        comodel_name='freight.purchase.quotation',
        inverse_name='route_id',
        string='Quotations'
    )

    total_quotations = fields.Char(
        string="Total Quotations",
        compute='_compute_total_quotation',
        store=False
    )

    @api.depends('from_location_id', 'to_location_id')
    def _compute_pol_pod(self):
        """Auto compute POL/POD from locations for sea routes"""
        for route in self:
            route.pol_id = False
            route.pod_id = False
            if route.transport_mode == constants.TransportMode.SEA:
                route.pol_id = route.from_location_id
                route.pod_id = route.to_location_id


    @api.constrains('pol_id', 'pod_id')
    def _check_ports(self):
        for route in self:
            if route.pol_id == route.pod_id:
                raise models.ValidationError("POL and POD cannot be the same!")
            
    @api.depends('quotation_ids')
    def _compute_total_quotation(self):
        for route in self:
            if route.quotation_ids:
                total = len(route.quotation_ids)
                route.total_quotations = f"{total} Quotation(s)"
            else:
                route.total_quotations = "0 Quotation(s)"