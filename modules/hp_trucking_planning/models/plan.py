from odoo import models, fields, api

class Plan(models.Model):
    _name = 'trucking_planning.plan'
    _description = 'Plan'
    _inherit = ['unique.code.mixin']
    _order = 'date asc'

    name = fields.Char(
        readonly=True,
    )
    date = fields.Date(
        string='Ngày đóng trả hàng',
        required=True,
        index=True,
    )
    vehicle_id = fields.Many2one(
        comodel_name='trucking_planning.vehicle',
        domain="[('type', '=', 'truck')]",
        required=True,
        index=True,
    )
    status = fields.Selection([
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ],default='active',
        required=True
    )
    plan_line_ids = fields.One2many(
        comodel_name='trucking_planning.plan.line',
        inverse_name='plan_id',
    )


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                seq = self.env['ir.sequence'].next_by_code('trucking_planning.plan') or '/'
                vals['name'] = seq
        return super().create(vals_list)

