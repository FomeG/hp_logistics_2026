from odoo import models, fields
from odoo.addons.hp_components.models import constants

class CsShippingInstruction(models.Model):
    _name = 'cs.shipping.instruction'
    _description = "Shipping Instruction"
    _inherit = ['cs.order.detail']

    booking_code = fields.Char(
        string="Booking Code",
        related="booking_id.code",
    )
    #todo: need to define partner_main_type
    shipper = fields.Many2one(
        comodel_name='res.partner',
        string="Shipper",
    )
    consignee = fields.Many2one(
        comodel_name='res.partner',
        string="Consignee",
    )
    notify_party = fields.Many2one(
        comodel_name='res.partner',
        string="Notify",
    )
    also_notify = fields.Many2one(
        comodel_name='res.partner',
        string="Notify",
    )
    incoterm_id = fields.Many2one(
        comodel_name='account.incoterms',
        string='Incoterm',
        related='cs_order_id.incoterm_id',
        store=True,
    )
    freight_charge = fields.Selection(
        constants.ShippingInstructions.FREIGHT_CHARGE_SELECT_OPTIONS,
        string="Freight & Charge"
    )
    cargo_description = fields.Text()
    #todo: recheck if these fields can be valuated by trucking team
    container_no = fields.Char(
        string="Container No",
    )
    seal_no = fields.Char(
        string="Seal No",
    )
    place_of_receipt = fields.Char(
        string="Place of Receipt"
    )
    place_of_issue = fields.Char(
        string="Place of Issue"
    )