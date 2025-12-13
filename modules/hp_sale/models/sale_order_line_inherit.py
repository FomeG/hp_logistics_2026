from odoo import models, fields


class SaleOrderLineInherit(models.Model):
    _inherit = 'sale.order.line'

    res_model_id = fields.Many2one(
        comodel_name='ir.model',
        string='Model Source Id',
        index=True,
        ondelete='cascade',
        help="currently source can be truck or sea freight"
    )
    res_model = fields.Char(
        string='Model Source Name',
        index=True,
        related='res_model_id.model',
        precompute=True,
        store=True,
        readonly=True
    )
    res_id = fields.Many2oneReference(
        string='Record Source Id',
        index=True,
        model_field='res_model'
    )
