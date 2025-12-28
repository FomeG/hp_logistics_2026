from odoo import models, fields
from odoo.addons.hp_components.models import constants


class CsBillLading(models.Model):
    _name = 'cs.bill.lading'
    _description = "Bill of Lading"
    _inherit = ['cs.order.detail']

    bl_number = fields.Char(
        string="BL Number",
        required=True,
    )
    bl_type = fields.Selection(
        constants.BL.SELECT_OPTIONS,
        required=True,
        default=constants.BL.MBL,
        string="BL Type",
    )
    issue_date = fields.Date()
    place_of_issue = fields.Char()

    vessel_id = fields.Many2one(
        related="booking_id.vessel_id",
        comodel_name='freight.purchase.vessel',
        string="Vessel",
        store=False,
    )
    pol_id = fields.Many2one(
        comodel_name='location.base',
        string="Port of Loading",
        related='booking_id.from_location_id',
        store=False,
    )
    pod_id = fields.Many2one(
        comodel_name='location.base',
        string="Port of Discharge",
        related='booking_id.to_location_id',
        store=False,
    )

    #todo check if related or filled by attachment file to verify