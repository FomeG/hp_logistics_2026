from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', compute=False)
    product_template_id = fields.Many2one('product.template', string='Product', compute=False)
    booking_id = fields.Many2one('pricing.booking', string='Booking')
    pod_name_request = fields.Char('POD name request')
    pod_id = fields.Many2one('pricing.pod', string="Port Of Discharge")
    pol_name_request = fields.Char('POL name request')
    pol_id = fields.Many2one('pricing.pol', string="Port Of Loading")
    etd = fields.Date(string="Estimated time of departure")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id')
    cost = fields.Monetary(string="Cost", currency_field='currency_id')
    
    project_type = fields.Char(string="Project Type", compute="_compute_project_type", store=False)
    is_quotation = fields.Boolean(compute='_compute_state_sale_order', store=False)
    is_product_has_price = fields.Boolean(compute='_compute_product_has_price', store=False)
    is_order_has_booking = fields.Boolean(compute='_compute_order_has_booking', store=False)
    booking_info = fields.Text(string="Booking Info", compute="_compute_booking_info", store=False)
    booking_ids = fields.Many2many(
        'pricing.booking',
        'project_task_booking_rel',
        'sale_order_id',
        'booking_id',
        string="Bookings"
    )

    @api.depends('booking_id')
    def _compute_booking_info(self):
        for record in self:
            if record.booking_id:
                record.booking_info = _("Voyage Name: %s\nPrice: %s\nContainer (qty-type): %s - %s, %s - %s") % (
                    record.booking_id.voyage_id.display_name or '',
                    record.booking_id.booking_price or '',
                    record.booking_id.volume_quantity_1 or '',
                    record.booking_id.volume_cont_1 or '',
                    record.booking_id.volume_quantity_2 or '',
                    record.booking_id.volume_cont_2 or '',
                )
            else:
                record.booking_info = ""
    
    @api.depends('project_id', 'project_id.type')
    def _compute_project_type(self):
        for task in self:
            task.project_type = task.project_id.type if task.project_id else False

    @api.depends('sale_order_id')
    def _compute_state_sale_order(self):
        for task in self:
            task.is_quotation = True if task.sale_order_id.state == 'draft' else False
    
    @api.depends('booking_id', 'product_template_id', 'sale_order_id')
    def _compute_product_has_price(self):
        for task in self:
            product = task.product_template_id
            sale_order_line = task.sale_order_id.order_line.filtered(lambda line: line.product_id.id == product.product_variant_id.id)
            task.is_product_has_price = True if product.booking_id.id == task.booking_id.id and sale_order_line else False

    @api.depends('sale_order_id')
    def _compute_order_has_booking(self):
        for task in self:
            task.is_order_has_booking = True if task.sale_order_id.booking_ids and task.booking_ids else False

    def update_done_task(self, pod_id = None, pol_id = None):
        done_stage = self.env['project.task.type'].search([('name', '=', 'Done')], limit=1)
        self.write({
            'stage_id': done_stage.id if done_stage else self.stage_id.id,
            'pod_id': pod_id,
            'pol_id': pol_id,
        })
        return True
    
    def action_show_sale_order_detail(self):
        self.ensure_one()
        return {
            'name': 'Sale Order Detail',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'new',
            'context': {'create': False, 'update': False, 'delete': False},
            'flags': {'mode': 'readonly'},
        }
    
    def action_confirm_quotation(self):
        self.n
        self.ensure_one()
        self.validate_action_submit('action_confirm_quotation')

        quotation = self.sale_order_id
        if quotation.state == 'draft' and quotation.action_confirm():
            self.update_done_task()
            self.message_post(body=_("Confirm quotation successfully."))
            return True
        raise UserError('Confirm quotation failed.')

    def action_approve_pod_pol(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_pod_pol')

        pod = self.env['pricing.pod'].create({
            'pod_name': self.pod_name_request,
            'region_id': self.env.user.region_id.id,
        })
        pol = self.env['pricing.pol'].create({
            'pol_name': self.pol_name_request
        })

        new_sealine = self.env['pricing.sealine'].search([('pod_id', '=', pod.id), ('pol_id', '=', pol.id)], limit=1)
        if new_sealine:
            new_product = self.env['product.template'].search([('sealine_id', '=', new_sealine.id)], limit=1)
            if new_product:
                self.update_done_task(pod.id, pol.id)
                # add sale order item
                sale_order = self.sale_order_id
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': new_product.product_variant_id.id,
                    'product_uom_qty': 1.0,
                    'name': new_product.name,
                })
                # create task request price
                project_request_price = self.env['project.project'].search([('type', '=', 'request_price')], limit=1)
                if project_request_price:
                    self.env['project.task'].create({
                        'name': new_product.name,
                        'project_id': project_request_price.id,
                        'sale_order_id': sale_order.id,
                        'product_template_id': new_product.id
                    })
                self.message_post(body=_("Create POD/POL successfully: %s, %s") % (self.pod_name_request, self.pol_name_request))
                return True
        raise UserError('Create POD/POL failed.')
    
    def action_approve_price(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_price')

        product = self.product_template_id
        product.write({
            'booking_id': self.booking_id.id,
            'list_price': self.sale_price,
            'standard_price': self.cost
        })
        # update price sale order line
        sale_order_line = self.sale_order_id.order_line.filtered(lambda line: line.product_id.id == product.product_variant_id.id)
        if sale_order_line:
            sale_order_line.write({
                'price_unit': self.sale_price
            })

        self.update_done_task()
        self.message_post(body=_("Approve price successfully with product: %s") % product.name)
        return True
    
    def action_approve_booking(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_booking')

        bookings = self.booking_ids
        self.sale_order_id.write({
            'booking_ids': [(6, 0, bookings.ids)]
        })
        self.update_done_task()

        booking_nos = ", ".join(str(bn) for bn in bookings.mapped('booking_no') if bn)
        self.message_post(body=_("Approve booking success with booking no: %s") % booking_nos)
        return True
    
    def validate_action_submit(self, action):
        match action:
            case 'action_approve_booking':
                if not self.sale_order_id:
                    raise ValidationError(_("Quotation is required."))
                if not self.booking_ids:
                    raise ValidationError(_("Booking is required."))
                
            case 'action_approve_pod_pol':
                if not self.pod_name_request:
                    raise ValidationError(_("POD name is required."))
                if not self.pol_name_request:
                    raise ValidationError(_("POL name is required."))
                
            case 'action_approve_price':
                if not self.product_template_id:
                    raise ValidationError(_("Product is required."))
                if not self.sale_price or not self.cost:
                    raise ValidationError(_("Sale price or Cost is not exist."))
                if not self.booking_id:
                    raise ValidationError(_("Booking is required."))

            case 'action_confirm_quotation':
                if not self.sale_order_id:
                    raise ValidationError(_("Quotation is not exist."))
            case _:
                return