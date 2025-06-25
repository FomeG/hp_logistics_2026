from odoo import models, fields, api


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
        tracking=True
    )
    pod_id = fields.Many2one(
        'freight.purchase.port',
        required=True,
        tracking=True
    )
    region_id = fields.Many2one(
        related='pod_id.region_id',
        store=True,
        tracking=True
    )
    shipment_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ],
        string='Shipment Type',
        required=True,
        tracking=True,
        compute='_compute_shipment_type',
        store=True,
    )
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    quotation_ids = fields.One2many('freight.purchase.quotation', 'route_id', string='Quotations')

    total_quotations = fields.Char(string="Total Quotations", compute='_compute_total_quotation', store=False)

    @api.depends('pol_id', 'pod_id')
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

    @api.depends('pol_id', 'pod_id')
    def _compute_shipment_type(self):
        for rec in self:
            if rec.pod_id.is_local:
                rec.shipment_type = 'import'
            elif rec.pol_id.is_local:
                rec.shipment_type = 'export'