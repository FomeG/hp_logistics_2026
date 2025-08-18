from odoo import models, api, fields
from odoo.exceptions import UserError
import base64
import math

class PlanLine(models.Model):
    _name = 'trucking_planning.plan.line'
    _description = 'Plan Line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'code'
    # _order = 'date asc'

    plan_id = fields.Many2one(
        comodel_name='trucking_planning.plan',
        string='Plan',
        required=True,
    )
    code = fields.Char(
        string='Job Number',
        tracking=True,
    )
    client_id = fields.Many2one(
        comodel_name='trucking_planning.client',
        required=True,
    )
    status = fields.Selection([
            ('hpl_reject','HPL Reject'),
            ('client_cancel','Client Cancel'),
            ('checking','Checking'),
            ('transfer','Transfer'),
            ('rented','Rented')
        ],
        string='Status',
        required=True,
        tracking=True,
    )
    plan_type = fields.Selection([],
        related='plan_id.plan_type',
        store=False,
    )
    route_id = fields.Many2one(
        comodel_name='trucking_planning.route', required=True
    )
    actual_source_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string='From Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    actual_destination_location_id = fields.Many2one(
        comodel_name='trucking_planning.location',
        compute='_compute_actual_locations',
        string = 'To Location',
        store=True,
        readonly=True,
        tracking=True,
    )
    note = fields.Text(string="Note")

    #goods info
    goods_name = fields.Char(
        string="Goods Name",
    )
    goods_weight = fields.Float(
        string="Goods Weight",
    )
    trip_ids = fields.One2many(
        comodel_name='trucking_planning.trip',
        string='Trip',
        inverse_name='plan_line_id',
    )


    # @api.depends('plan_id.date')
    # def _compute_plan_month_year(self):
    #     for record in self:
    #         if record.plan_id.date:
    #             record.plan_month = record.plan_id.date.month
    #             record.plan_year = record.plan_id.date.year
    #         else:
    #             record.plan_month = False
    #             record.plan_year = False

    @api.depends('plan_type', 'route_id')
    def _compute_actual_locations(self):
        for rec in self:
            if rec.route_id:
                if rec.plan_type == 'export':
                    rec.actual_source_location_id = rec.route_id.from_location_id
                    rec.actual_destination_location_id = rec.route_id.to_location_id
                else:  # import
                    rec.actual_source_location_id = rec.route_id.to_location_id
                    rec.actual_destination_location_id = rec.route_id.from_location_id
            else:
                rec.actual_source_location_id = False
                rec.actual_destination_location_id = False

    def _compute_route_info(self):
        for trip in self:
            freeway_text = '(freeway)' if trip.freeway else ''
            trip.route_info = f"{trip.actual_source_location_id.name} - {trip.actual_destination_location_id.name} {freeway_text}"

    def _compute_container_info(self):
        for trip in self:
            trip.container_info = f"{trip.container_type},{trip.container_size}"

    def _compute_location_info(self):
        for trip in self:
            contact_info = f"({trip.contact_phone})" if trip.contact_phone else ""
            trip.location_info = f"{trip.container_pickup.name},{trip.goods_pickup_delivery.name} {contact_info},{trip.container_delivery.name}"

    def _compute_driver_info(self):
        for trip in self:
            trip.driver_info = f"{trip.driver_id.name},{trip.truck_id.name}"

    @api.onchange('route_id')
    def _on_route_change(self):
        for trip in self:
            trip.plan_type = trip.route_id.direction

    def action_view_trips(self):
        """Action để xem tất cả trips thuộc plan line này"""
        self.ensure_one()
        return {
            'name': f'Trips - {self.code or self.plan_id.name}',
            'res_model': 'trucking_planning.trip',
            'view_mode': 'list,form',
            'domain': [('plan_line_id', '=', self.id)],
            'context': {
                'default_plan_line_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'target': 'current',
        }