from odoo import models, fields, api
from odoo.exceptions import ValidationError
from ..validators.region_validator import RegionCreateValidator, RegionUpdateValidator

class FreightPurchaseRegion(models.Model):
    _description = 'Region'
    _inherit = ['region']
    _order = 'create_date desc'

    ports = fields.One2many('location.base','region_id',string='Ports', tracking=True)
    port_string = fields.Char(string="Ports in Region", compute='_compute_port_string', store=False)

    @api.depends('employee_ids')
    def _compute_employee_string(self):
        for region in self:
            if region.employee_ids:
                region.employee_string = ", ".join(region.employee_ids.mapped('name'))
            else:
                region.employee_string = ""

    @api.depends('country_ids.port_ids')
    def _compute_port_string(self):
        for region in self:
            ports = region.country_ids.mapped('port_ids.name')
            region.port_string = ", ".join(ports) if ports else ""

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            validated, errors = RegionCreateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().create(vals_list)
    
    def write(self, vals):
        for record in self:
            validated, errors = RegionUpdateValidator.validate(vals, self.env)
            if errors:
                raise ValidationError("\n".join([f"• {e}" for e in errors]))
        return super().write(vals)