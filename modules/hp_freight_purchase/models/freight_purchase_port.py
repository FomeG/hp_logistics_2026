# from pkg_resources import require
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.port_validator import PortCreateValidator, PortUpdateValidator
from odoo.addons.hp_components.models import constants


class FreightPurchasePort(models.Model):
    _inherit = ['location.base']
    _description = 'Port'
    _order = 'create_date desc'

    # _name = 'freight.purchase.port'
    # name = fields.Char(required=True, tracking=True)
    # is_local = fields.Boolean(
    #     string='Is Local Port',
    #     required=False,
    #     default=False,
    #     tracking=True
    # )
    # country_id = fields.Many2one('res.country', string='Country', required=True, tracking=True, ondelete='cascade')

    # region_id = fields.Many2one(
    #     comodel_name='region',
    #     string='Region',
    #     related='country_id.region_id',
    #     tracking=True
    # )
    is_active = fields.Boolean(
        string='Is Active',
        default=True,
        tracking=True
    )
    employees = fields.Char(
        string="Employees in Region",
        compute='_compute_region_employees',
        store=False
    )

    @api.onchange('country_id')
    def _onchange_country_id(self):
        for record in self:
            if record.country_id and record.country_id.code == 'VN':
                record.is_local = True
            else:
                record.is_local = False
    @api.constrains('region_id')
    def _check_region_required(self):
        for record in self:
            if not record.region_id:
                raise ValidationError("Region is required for the port.")

    @api.depends('region_id.employee_ids')
    def _compute_region_employees(self):
        for port in self:
            if port.region_id and port.region_id.employee_ids:
                port.employees = ", ".join(port.region_id.employee_ids.mapped('name'))
            else:
                port.employees = ""
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = PortCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            validated, errors = PortUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)