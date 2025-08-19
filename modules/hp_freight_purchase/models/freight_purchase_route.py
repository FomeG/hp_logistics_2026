from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.route_validator import RouteCreateValidator, RouteUpdateValidator

class FreightPurchaseRoute(models.Model):
    _name = 'freight.purchase.route'
    _description = 'Route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Route Name',
        compute='_compute_route_name',
        store=True,
        index=True,
        tracking=True
    )
    pol_id = fields.Many2one(
        'freight.purchase.port',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    pod_id = fields.Many2one(
        'freight.purchase.port',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    direction = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('N/A', 'N/A'),
    ],
        required=True,
        compute='_compute_direction',
        default='export',
        inverse='_inverse_direction',
        store=True
    )
    direction_manual = fields.Boolean(string="Manual Direction", default=False)
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    quotation_ids = fields.One2many('freight.purchase.quotation', 'route_id', string='Quotations')

    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('pol_id.name', 'pod_id.name')
    def _compute_route_name(self):
        for route in self:
            if route.pod_id and route.pol_id:
                route.name = f"{route.pol_id.name} → {route.pod_id.name}"
            else:
                route.name = False
            

    # Constraints
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

    def _inverse_direction(self):
        for rec in self:
            rec.direction_manual = True

    @api.depends('pol_id.is_local', 'pod_id.is_local')
    def _compute_direction(self):
        for rec in self:
            if rec.direction_manual:
                continue
            if rec.pod_id and rec.pod_id.is_local:
                rec.direction = 'import'
            elif rec.pol_id and rec.pol_id.is_local:
                rec.direction = 'export'
            else:
                rec.direction = 'N/A'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = RouteCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            self._check_pol_pod(vals.get('pol_id'), vals.get('pod_id'))
        return super().create(vals_list)
    
    def write(self, vals):
        for record in self:
            validated, errors = RouteUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
            pol_id = vals.get('pol_id', self.pol_id.id)
            pod_id = vals.get('pod_id', self.pod_id.id)
            self._check_pol_pod(pol_id, pod_id)
        return super().write(vals)


    def _check_pol_pod(self, pol_id, pod_id):
        pol = self.env['freight.purchase.port'].browse(pol_id)
        pod = self.env['freight.purchase.port'].browse(pod_id)
        
        if pol.is_local == pod.is_local:
            raise ValidationError(
                f"Route from {pol.name} to {pod.name} is invalid: "
                f"POL and POD cannot both be local or both be non-local."
            )