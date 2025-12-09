from odoo import models, fields, api
from odoo.addons.hp_components.models import constants

class CsShippingDocument(models.Model):
    _name = "cs.shipping.document"
    _inherit = ['cs.order.detail', 'mail.thread', 'mail.activity.mixin']
    _description = "Customer Service Shipping Document"

    name = fields.Char(
        required=True,
        readonly=True,
        store=True,
        compute='_compute_name',
        tracking=True,
    )

    instruction_type = fields.Selection(
        constants.ShippingDocumentType.SELECT_OPTIONS,
        required=True,
        string="Instruction Type",
        tracking=True,
    )
    document_number = fields.Char(
        string="DO/AN Number",
        required=True,
        tracking=True,
        help="Delivery Order (DO) or Arrival Notice (AN) number",
    )


    state = fields.Selection(
        constants.ShippingDocumentState.SELECT_OPTIONS,
        string="State",
        default=constants.ShippingDocumentState.DRAFT,
        tracking=True,
        required=True,
    )

    note = fields.Text(
        string="Note",
        tracking=True,
    )

    cs_shipping_instruction_id = fields.Many2one(
        comodel_name='cs.shipping.instruction',
        string="Related Shipping Instruction",
        compute='_compute_shipping_instruction',
        store= True,
    )

    shipper_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shipper',
        required=True,
        related='cs_shipping_instruction_id.shipper',
        store=True,
        readonly=False,
        help='Thông tin bên gửi hàng'
    )

    consignee_id = fields.Many2one(
        comodel_name='res.partner',
        string='Consignee',
        required=True,
        related='cs_shipping_instruction_id.consignee',
        store=True,
        readonly=False,
    )

    notify_party_id = fields.Many2one(
        comodel_name='res.partner',
        string='Notify Party',
        related='cs_shipping_instruction_id.notify_party',
        store=True,
        readonly=False,
    )

    contact_name = fields.Char(
        string="Contact Name",
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        tracking=True,
    )

    contact_phone = fields.Char(
        string="Contact Phone",
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        tracking=True,
    )

    contact_tax_code = fields.Char(
        string='MST',
        compute='_compute_contact_info',
        store=True,
        readonly=False,
        help='Mã số thuế (mặc định lấy từ client)'
    )

    cs_bill_lading_id = fields.Many2one(
        comodel_name='cs.bill.lading',
        string="Bill of Lading",
        compute='_compute_bill_lading_info',
        domain="[('cs_order_id', '=', cs_order_id)]",
        tracking=True,
    )

    issue_date = fields.Date(
        string="Issue Date",
        related='cs_bill_lading_id.issue_date',
        tracking=True,
    )

    bl_number = fields.Char(
        string="MBL/HBL Number",
        tracking=True,
        related='cs_bill_lading_id.bl_number',
        store=True,
    )

    vessel_name = fields.Char(
        string='Vessel Name',
        related='booking_id.vessel_id.name',
        store=True,
        help='Vessel Name from Booking',
    )

    voyage = fields.Char(
        string='Voyage',
        related='booking_id.voyage',
        store=True,
        help='Voyage from Booking',
    )

    pol_id = fields.Many2one(
        comodel_name='location.base',
        string='Port of Loading',
        related='booking_id.from_location_id',
        store=True,
    )

    pod_id = fields.Many2one(
        comodel_name='location.base',
        string='Port of Discharge',
        related='booking_id.to_location_id',
        store=True,
    )

    place_of_receipt = fields.Char(
        string='Place of Receipt',
        related='cs_shipping_instruction_id.place_of_receipt',
        store=True,
    )

    place_of_delivery = fields.Char(
        string='Place of Delivery',
        compute='_compute_place_of_delivery',
        store=True,
        readonly=True,
    )

    etd = fields.Date(
        string='Estimate of Departure',
        related='booking_id.etd',
        store=True,
    )

    eta = fields.Datetime(
        string='Estimate of Arrival',
        related='cs_order_id.estimate_time_arrival',
        store=True,
    )

    container_line_ids = fields.One2many(
        comodel_name='cs.container',
        inverse_name='shipping_document_id',
        string='Danh sách Container',
        required=True,
        help='Chi tiết container cần giao'
    )

    @api.depends('cs_order_id', 'cs_order_id.cs_bill_lading_ids',
                 'cs_order_id.cs_bill_lading_ids.issue_date')
    def _compute_bill_lading_info(self):
        for record in self:
            bls = record.cs_order_id.cs_bill_lading_ids

            if bls:
                first_bl = bls[0]
                record.cs_bill_lading_id = first_bl.id
            else:
                record.cs_bill_lading_id = False

    @api.depends('cs_order_id', 'cs_order_id.cs_shipping_instruction_id')
    def _compute_shipping_instruction(self):
        for record in self:
            if record.cs_order_id and record.cs_order_id.cs_shipping_instruction_id:
                # cs_shipping_instruction_id là One2many nên lấy record đầu tiên
                shipping_instructions = record.cs_order_id.cs_shipping_instruction_id
                if shipping_instructions:
                    record.cs_shipping_instruction_id = shipping_instructions[0].id
                else:
                    record.cs_shipping_instruction_id = False
            else:
                record.cs_shipping_instruction_id = False

    @api.depends('document_number')
    def _compute_name(self):
        for record in self:
            record.name = record.document_number

    @api.depends('cs_order_id', 'cs_order_id.service_type',
                 'cs_order_id.goods_delivery_location_id',
                 'cs_order_id.actual_destination_location_id')
    def _compute_place_of_delivery(self):
        """
        Export → actual_destination_location_id (cảng/depot đích)
        Import → goods_delivery_location_id (nơi giao hàng cho khách)
        """
        for record in self:
            if not record.cs_order_id:
                record.place_of_delivery = False
                continue

            cs_order = record.cs_order_id

            if cs_order.service_type == 'export':
                location = cs_order.actual_destination_location_id
            else:
                location = cs_order.goods_delivery_location_id

            record.place_of_delivery = location.name if location else False

    @api.depends('cs_order_id')
    def _compute_contact_info(self):
        """
        Lấy mặc định thông tin từ Client (trong Sale Order của CS Order).
        """
        for record in self:
            client = record.cs_order_id.sale_order_id.client_id
            if client:
                record.contact_name = client.name
                record.contact_phone = client.phone
                # Lấy MST (thường là field 'vat' trong Odoo, nếu model client khác thì cần sửa lại)
                record.contact_tax_code = client.vat if hasattr(client, 'vat') else False
            else:
                record.contact_name = False
                record.contact_phone = False
                record.contact_tax_code = False

