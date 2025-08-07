from odoo import models, fields, api
import re
import calendar

class Vehicle(models.Model):
    _name = 'trucking_planning.vehicle'
    _description = 'Trucking Planning Vehicle'
    _inherit = ['unique.normalized.name.mixin', 'mail.thread', 'mail.activity.mixin']

    type = fields.Selection([
        ('truck', 'Truck'),
        ('trailer', 'Trailer'),
    ],
        default='truck',
        index=True,
        required=True,
        string="Type",
        tracking=True,
    )
    name = fields.Char(
        string='Number',
        required=True,
        tracking=True,
    )
    engine_type = fields.Selection([
        ('small','Small'),
        ('big','Big'),
    ],default='small', string="Engine Type", tracking=True)

    trailer_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        string='Trailer',
        domain=[
            ('active', '=', True),
            ('type','=','trailer'),
        ],
        index=True,
    )

    primary_driver_id = fields.Many2one(
        comodel_name='trucking_planning.driver',
        domain="[('active', '=', True)]",
        index=True,
    )
    fuel_rate_inferior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        store=True,
        string='Light',
        tracking=True,
    )
    fuel_rate_superior_20 = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        store=True,
        string='Heavy',
        tracking=True,
    )
    fuel_rate_mix = fields.Float(
        compute='_compute_fuel_rates',
        default=0.0,
        store=True,
        string='Mix',
        tracking=True,
    )
    registration_date = fields.Date(
        string='Registration Date',
        tracking=True,
    )
    is_rented = fields.Boolean(
        string='Is rented',
        default=False,
        tracking=True,
    )
    active = fields.Boolean(
        default=True,
        tracking=True,
    )
    plan_ids = fields.One2many(
        comodel_name='trucking_planning.plan',
        string='Plans',
        inverse_name='vehicle_id',
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        string='Trips',
        inverse_name='truck_id',
    )
    vehicle_driver_history_ids = fields.One2many(
        comodel_name='trucking_planning.vehicle.driver.history',
        inverse_name='vehicle_id',
    )
    total_plan_in_month = fields.Integer(string="Total Plan In Month", compute='_compute_total_plan_in_month', store=False)
    is_available_on_date = fields.Boolean(
        string='Available on Date Plan',
        compute='_compute_is_available_on_date',
        search='_search_is_available_on_date'
    )
    
    @api.depends('plan_ids.date')
    def _compute_total_plan_in_month(self):
        today = fields.Date.today()
        month_start = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day)

        plan = self.env['trucking_planning.plan']

        for rec in self:
            rec.total_plan_in_month = plan.search_count([
                ('vehicle_id', '=', rec.id),
                ('date', '>=', month_start),
                ('date', '<=', month_end),
            ])

    @api.depends('plan_ids', 'plan_ids.date')
    def _compute_is_available_on_date(self):
        check_date = self.env.context.get('check_date', fields.Date.today())
        for vehicle in self:
            vehicle.is_available_on_date = not any(
                plan.date == check_date for plan in vehicle.plan_ids
            )
    
    def _search_is_available_on_date(self, operator, value):
        check_date = self.env.context.get('check_date', fields.Date.today())
        busy_vehicle_ids = self.env['trucking_planning.plan'].search([
            ('date', '=', check_date)
        ]).mapped('vehicle_id.id')

        return [('id', 'not in', busy_vehicle_ids)]
    

    @api.depends('type', 'engine_type')
    def _compute_fuel_rates(self):
        for vehicle in self:
            if vehicle.type != 'truck':
                vehicle.fuel_rate_inferior_20 = 0.0
                vehicle.fuel_rate_superior_20 = 0.0
                vehicle.fuel_rate_mix = 0.0
                continue

            if vehicle.engine_type == 'small':
                vehicle.fuel_rate_inferior_20 = 0.32
                vehicle.fuel_rate_superior_20 = 0.35
                vehicle.fuel_rate_mix = 0.38
            else:  # big engine
                vehicle.fuel_rate_inferior_20 = 0.35
                vehicle.fuel_rate_superior_20 = 0.38
                vehicle.fuel_rate_mix = 0.42

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = self._clean_license_plate(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = self._clean_license_plate(vals['name'])
        return super().write(vals)

    def _clean_license_plate(self, plate):
        return re.sub(r'[^A-Za-z0-9-]', '', plate)