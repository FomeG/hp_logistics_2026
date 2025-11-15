from odoo import models, fields


class CsContainer(models.Model):
    _name = "cs.container"
    _description = "Container Information"
    _inherit = ['cs.order.detail']

    container_type_id = fields.Many2one(
        comodel_name='container.type',
        string="Container Type"
    )
    container_number = fields.Char(
        string="Container No"
    )
    seal_number = fields.Char(
        string="Seal No"
    )
    gross_weight = fields.Float(
        string="Gross Weight (KG)"
    )
    net_weight = fields.Float(
        string="Net Weight (KG)"
    )
    note = fields.Text()

