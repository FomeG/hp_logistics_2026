from odoo import models, fields, api
from odoo.addons.hp_components.models import constants

class CsOrder(models.Model):
    _name = 'cs.order'
    _inherits = {'project.project': 'project_id'}
    _inherit = ['mail.thread'] # mail activity already have field attachment id so if we add field attachment id in other order it will give error

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        required=True,
        ondelete='cascade',
        index=True,
    )

    batch_order_id = fields.Many2one(
        comodel_name='cs.batch.order',
        string="Batch Order",
        help="used for monthly billing"
    )
    code = fields.Char(
        string="Cs Ref",
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        index=True,
    )

    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
    )
    incoterm_id = fields.Many2one(
        comodel_name='account.incoterms',
        string='Incoterm',
        related='sale_order_id.incoterm_id',
        store=True,
    )
    booking_id = fields.Many2one(
        comodel_name='freight.purchase.booking',
        related='sale_order_id.booking_id',
    )
    state = fields.Selection(
        constants.CsOrderState.SELECT_OPTIONS,
        string="State",
        default=constants.CsOrderState.DRAFT,
        required=True,
    )
    note = fields.Text()
    delivery_term = fields.Selection(
        constants.DeliveryTerms.SELECT_OPTIONS,
        string="Delivery Term",
        default=constants.DeliveryTerms.CY_CY,
        help=""
            "cy-cy: Delivery from port of departure container yard → port of destination container yard\n"
            "door-cy: Pick up from the shipper's warehouse → deliver to the port of destination container yard\n"
            "cy-door:Delivery from port of departure → to the receiver's warehouse\n"
            "door-door:Delivery from shipper's warehouse → receiver's warehouse",
        required=True,
    )
    service_type = fields.Selection( #service type from sale order is selection
        constants.ServiceType.SELECT_OPTIONS,
        related='sale_order_id.service_type',
        string="Service Type",
        help="Import/Export/Other Service",
        store=False,
    )
    order_name = fields.Char(
        related='sale_order_id.name',
        string='Order Reference',
        index=True,
    )
    salesman_id = fields.Many2one(
        comodel_name='res.users',
        related='sale_order_id.user_id',
        string='Salesman',
        index=True,
    )
    client_id = fields.Many2one(
        comodel_name='res.partner.client',
        related='sale_order_id.client_id',
        string='Client',
        index=True,
    )
    commodity = fields.Char(
        related='sale_order_id.commodity',
        store=False,
    )
    commodity_hs_code = fields.Char(
        string="Commodity HS Code",
        store=False,
    )

    cs_booking_id = fields.One2many(
        comodel_name="cs.booking",
        inverse_name="cs_order_id",
        string="Booking",
        limit=1
    )
    Booking_code = fields.Char(
        related='cs_booking_id.Booking_code',
        string="Booking Code",
        help="Booking Code",
        index=True,
        store=True,
        readonly=True,
    )
    cs_shipping_instruction_id = fields.One2many(
        comodel_name="cs.shipping.instruction",
        inverse_name="cs_order_id",
        string="Shipping Instruction",
        limit=1
    )
    cs_bill_lading_ids = fields.One2many(
        comodel_name="cs.bill.lading",
        inverse_name="cs_order_id",
        string="BLs",
    )
    cs_pre_alert_id = fields.One2many(
        comodel_name="cs.pre.alert",
        inverse_name="cs_order_id",
        limit=1
    )
    cs_container_ids = fields.One2many(
        comodel_name="cs.container",
        inverse_name="cs_order_id",
        string = "Containers",
    )
    cs_debit_id = fields.One2many(
        comodel_name="cs.debit",
        inverse_name="cs_order_id",
        string = "Debits",
    )
    cs_task_ids = fields.One2many(
        comodel_name="cs.task",
        inverse_name="cs_order_id",
        string = "Tasks",
    )

    @api.model
    def create_from_sale_order(self, sale_order):
        cs_batch_order_id = False
        if sale_order.is_monthly_billing:
            cs_batch_order = self.env['cs.batch.order'].sudo().get_or_create_from_sale_order(sale_order)
            cs_batch_order_id = cs_batch_order.id

        code = self.env['cs.service'].generate_code_from_sale_order(sale_order,'cs.order')
        self.create({
            'name': code, # name is required
            'batch_order_id': cs_batch_order_id,
            'code': code,
            'user_id': self.env.user.id,
            'sale_order_id': sale_order.id,
            'state': constants.CsOrderState.DRAFT,
        })

