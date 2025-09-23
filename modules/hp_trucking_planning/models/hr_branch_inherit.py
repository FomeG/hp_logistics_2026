from odoo import models, fields, api

class HrBranchInherit(models.Model):
    _inherit = ['hr.branch']

    vehicle_ids = fields.One2many(
        comodel_name='fleet.vehicle.hpl',
        inverse_name='branch_id',
        string='vehicles'
    )

    total_vehicles =  fields.Integer(string="Total vehicles", compute="_compute_total_vehicle", store=False)


    @api.depends('vehicle_ids')
    def _compute_total_vehicle(self):
        for rec in self:
            rec.total_vehicles = len(rec.vehicle_ids)