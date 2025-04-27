from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from odoo.addons.hp_pricing.models.inherit_res_users import get_excluded_user_ids

_logger = logging.getLogger(__name__)

class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    sale_order_id = fields.Many2one('sale.order', string='Sales Order', compute=False)
    product_template_id = fields.Many2one('product.template', string='Product', compute=False)
    booking_id = fields.Many2one('pricing.booking', string='Booking')
    region_id = fields.Many2one('pricing.region', string='Region')
    pod_name_request = fields.Char('POD name request')
    pod_id = fields.Many2one('pricing.pod', string="Port Of Discharge")
    pol_name_request = fields.Char('POL name request')
    pol_id = fields.Many2one('pricing.pol', string="Port Of Loading")
    etd = fields.Date(string="Estimated time of departure")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id')
    cost = fields.Monetary(string="Cost", currency_field='currency_id')

    start_time = fields.Datetime(string="Start Time", readonly=True)
    end_time = fields.Datetime(string="End Time", readonly=True)
    
    project_type = fields.Char(string="Project Type", compute="_compute_project_type", store=False)
    is_quotation = fields.Boolean(compute='_compute_state_sale_order', store=False)
    is_product_has_price = fields.Boolean(compute='_compute_product_has_price', store=False)
    is_order_has_booking = fields.Boolean(compute='_compute_order_has_booking', store=False)
    booking_info = fields.Text(string="Booking Info", compute="_compute_booking_info", store=False)
    is_project_pricing = fields.Boolean(compute="_check_project_pricing", store=False)
    is_done = fields.Boolean(string="Is Done", compute="_compute_is_done", store=False)

    sale_line_id = fields.Many2one(
        'sale.order.line',
        string='Sales Order Line',
        compute='_compute_sale_line_id',
        store=True,
        help="Related sale order line for this task"
    )

    approval_type = fields.Selection([
        ('sale_leader', 'Sales Leader Approval'),
        ('pricing_leader', 'Pricing Leader Approval')
    ], string="Approval Type")

    allowed_region_ids = fields.Many2many('pricing.region', compute='_compute_allowed_region_ids')

    @api.depends('project_type')
    def _compute_allowed_region_ids(self):
        for task in self:
            if task.project_type == 'request_product':
                # Check if current user is pricing lead or director
                is_pricing_lead = self.env.user.has_group('hp_pricing.group_hp_pricing_lead')
                is_pricing_director = self.env.user.has_group('hp_pricing.group_hp_pricing_director')

                if is_pricing_lead or is_pricing_director:
                    # Allow all regions for lead and director
                    task.allowed_region_ids = self.env['pricing.region'].search([])
                else:
                    # Only allow regions where the current user is a member
                    task.allowed_region_ids = self.env.user.region_id
            else:
                # For other task types, allow all regions
                task.allowed_region_ids = self.env['pricing.region'].search([])

    @api.constrains('user_ids', 'project_type')
    def _check_user_region(self):
        for task in self:
            # Only validate for request_product tasks
            if task.project_type == 'request_product':
                for user in task.user_ids:
                    if user.has_group('hp_pricing.group_hp_pricing_member') and not user.has_group(
                            'hp_pricing.group_hp_pricing_lead') and not user.has_group(
                            'hp_pricing.group_hp_pricing_director'):
                        if not user.region_id:
                            raise ValidationError(
                                _("User '%s' is a pricing member but is not assigned to any region yet, please add him/her to a region before assigning.") % user.name)

    @api.depends('stage_id')
    def _compute_is_done(self):
        for task in self:
            name = task.stage_id.name
            task.is_done = name and name.lower() == 'done'

    @api.constrains('sale_line_id')
    def _check_sale_line_type(self):
        for task in self.sudo():
            if task.sale_line_id:
                # Allow your custom product types
                if task.sale_line_id.product_id.type not in ['pricing', 'trucking', 'common',
                                                             'custom'] or task.sale_line_id.is_expense:
                    raise ValidationError(_(
                        'You cannot link the order item %(order_id)s - %(product_id)s to this task because it is a re-invoiced expense.',
                        order_id=task.sale_line_id.order_id.name,
                        product_id=task.sale_line_id.product_id.display_name,
                    ))

    @api.depends('sale_order_id', 'product_template_id')
    def _compute_sale_line_id(self):
        for task in self:
            if task.sale_order_id and task.product_template_id:
                matching_line = task.sale_order_id.order_line.filtered(
                    lambda line: line.product_id.product_tmpl_id.id == task.product_template_id.id
                )
                task.sale_line_id = matching_line[0].id if matching_line else False
            else:
                task.sale_line_id = False

    def write(self, vals):
        stage_obj = self.env['project.task.type']
        new_stage_id = vals.get('stage_id', False)
        for task in self:
            current_stage = task.stage_id
            if current_stage and current_stage.name.lower() == "done":
                raise UserError(_("Cannot update a done Task"))

            if new_stage_id:
                new_stage = stage_obj.browse(new_stage_id)
                if new_stage and new_stage.name.lower() == "in progress" and not task.start_time:
                    vals['start_time'] = datetime.now()
                elif new_stage and new_stage.name.lower() == "done" and not task.end_time:
                    vals['end_time'] = datetime.now()

        return super().write(vals)
    
    @api.depends('project_id')
    def _check_project_pricing(self):
        for task in self:
            task.is_project_pricing = True if task.project_id.type in task.project_id.PROTECTED_TYPE else False

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
    
    @api.depends('product_template_id', 'sale_order_id')
    def _compute_product_has_price(self):
        for task in self:
            product = task.product_template_id
            sale_order_line = task.sale_order_id.order_line.filtered(lambda line: line.product_id.id == product.product_variant_id.id)
            task.is_product_has_price = True if sale_order_line and sale_order_line.booking_id and sale_order_line.base_price else False

    @api.depends('sale_line_id', 'booking_id')
    def _compute_order_has_booking(self):
        for task in self:
            task.is_order_has_booking = True if task.booking_id and task.sale_line_id.booking_id.id == task.booking_id.id else False

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

    def action_show_sale_order_line_detail(self):
        self.ensure_one()
        return {
            'name': 'Sale Order Line Detail',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'form',
            'res_id': self.sale_line_id.id,
            'target': 'new',
            'context': {'create': False, 'update': False, 'delete': False},
            'flags': {'mode': 'readonly'},
        }
    
    def action_show_product_detail(self):
        self.ensure_one()
        return {
            'name': 'Product Detail',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'form',
            'res_id': self.product_template_id.id,
            'target': 'new',
            'context': {'create': False, 'update': False, 'delete': False},
            'flags': {'mode': 'readonly'},
        }

    # Add rejection reason field to handle the rejection cases
    rejection_reason = fields.Text(string='Rejection Reason')

    def action_sale_leader_approve(self):
        """Approve quotation by sales leader and create task for pricing leader"""
        self.ensure_one()

        # Validate the action
        if not self.sale_order_id or self.sale_order_id.state != 'customer_confirm':
            raise ValidationError(_("This quotation cannot be approved in its current state."))

        # Update quotation state to sale_leader_confirm
        self.sale_order_id.sudo().action_sale_leader_approved()

        # Mark the task as done
        self.update_done_task()

        # Post a message in the chatter
        self.message_post(body=_("Quotation approved by sales leader."))
        return True

    def action_sale_leader_reject(self):
        """Reject quotation by sales leader"""
        self.ensure_one()

        # Validate the action
        if not self.sale_order_id or self.sale_order_id.state != 'customer_confirm':
            raise ValidationError(_("This quotation cannot be rejected in its current state."))

        # Check if rejection reason is provided
        if not self.rejection_reason:
            raise ValidationError(_("Please provide a reason for rejection."))

        # Handle rejection logic here
        # You might want to set the quotation back to draft or another state
        self.sale_order_id.sudo().write({'state': 'activated'})

        # Mark the task as done
        self.update_done_task()

        # Post a message in the chatter
        self.message_post(body=_("Quotation rejected by sales leader and set back to Activated state. Reason: %s") % self.rejection_reason)
        return True

    def action_pricing_leader_approve(self):
        """Approve quotation by pricing leader and confirm order"""
        self.ensure_one()

        # Validate the action
        if not self.sale_order_id or self.sale_order_id.state != 'sale_leader_confirm':
            raise ValidationError(_("This quotation cannot be approved in its current state."))

        # Update quotation state to pricing_leader_confirm
        self.sale_order_id.sudo().action_pricing_leader_approved()

        # Mark the task as done
        self.update_done_task()

        # Post a message in the chatter
        self.message_post(body=_("Quotation approved by pricing leader."))
        return True

    def action_pricing_leader_reject(self):
        """Reject quotation by pricing leader"""
        self.ensure_one()

        # Validate the action
        if not self.sale_order_id or self.sale_order_id.state != 'sale_leader_confirm':
            raise ValidationError(_("This quotation cannot be rejected in its current state."))

        # Check if rejection reason is provided
        if not self.rejection_reason:
            raise ValidationError(_("Please provide a reason for rejection."))

        # Handle rejection logic here
        # You might want to set the quotation back to customer_confirm
        self.sale_order_id.sudo().write({'state': 'customer_confirm'})

        # Mark the task as done
        self.update_done_task()

        # Post a message in the chatter
        self.message_post(body=_("Quotation rejected by pricing leader. Reason: %s") % self.rejection_reason)
        return True

    # Avoiding order to be confirmed from project/task
    def _ensure_sale_order_linked(self, sol_ids):
        if self.env.context.get('skip_so_confirmation'):
            return
        return super()._ensure_sale_order_linked(sol_ids)

    def action_approve_pod_pol(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_pod_pol')

        pol = self.env['pricing.pol'].search([('pol_name', 'ilike', self.pol_name_request)], limit=1)
        pod = self.env['pricing.pod'].search([('pod_name', 'ilike', self.pod_name_request)], limit=1)
        if not pod:
            pod = self.env['pricing.pod'].create({
                'pod_name': self.pod_name_request,
                'region_id': self.region_id.id,
            })
        if not pol:
            pol = self.env['pricing.pol'].create({
                'pol_name': self.pol_name_request
            })

        new_sealine = self.env['pricing.sealine'].search([('pod_id', '=', pod.id), ('pol_id', '=', pol.id)], limit=1)
        if new_sealine:
            new_product = self.env['product.template'].search([('sealine_id', '=', new_sealine.id)], limit=1)
            if new_product:
                # add sale order item
                sale_order = self.sale_order_id
                # Create new sealine
                new_sale_line = self.env['sale.order.line'].sudo().create({
                    'order_id': sale_order.id,
                    'product_id': new_product.product_variant_id.id,
                    'product_uom_qty': 1.0,
                    'name': new_product.name,
                    'product_type_filter': 'pricing'
                })

                # create task request price
                project_request_price = self.env['project.project'].search([('type', '=', 'request_price')], limit=1)
                if project_request_price:
                    # Get list of users to exclude
                    excluded_ids = get_excluded_user_ids(self.env)

                    pricing_director_group = self.env.ref('hp_pricing.group_hp_pricing_director')
                    pricing_director = self.env['res.users'].search([
                        ('groups_id', 'in', pricing_director_group.id),
                        ('id', 'not in', excluded_ids),
                        ('active', '=', True)
                    ], limit=1)

                    assignee_ids = []
                    if pricing_director:
                        assignee_ids.append(pricing_director.id)

                    # Create a new task for request_price with assignees
                    task_vals = {
                        'name': new_product.name,
                        'project_id': project_request_price.id,
                        'sale_order_id': sale_order.id,
                        'sale_line_id': new_sale_line.id,
                        'product_template_id': new_product.id,
                        'etd': self.etd,
                        'date_assign': datetime.now(),
                    }

                    # Add assignees if found
                    if assignee_ids:
                        task_vals['user_ids'] = [(6, 0, assignee_ids)]

                    self.env['project.task'].sudo().with_context(skip_so_confirmation=True).create(task_vals)
                    sale_order.write({'state': 'activated'})
                self.update_done_task(pod.id, pol.id)
                self.send_notification_by_stage('done')
                self.message_post(body=_("Create POD/POL successfully: %s, %s") % (self.pod_name_request, self.pol_name_request))

                return True
        raise UserError('Create POD/POL failed.')

    @api.onchange('etd')
    def _onchange_etd_set_booking_domain(self):
        if self.etd:
            return {
                'domain': {
                    'booking_id': [('voyage_id.etd', '>=', self.etd)]
                }
            }

    @api.onchange('booking_id')
    def _onchange_booking_id(self):
       self.etd = self.booking_id.voyage_id.etd

    # Update booking => base price for sale order line
    def action_approve_price(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_price')

        # Find and update the matching sale order line
        if self.sale_line_id:
            self.sale_line_id.sudo().write({
                'booking_id': self.booking_id.id,
                'base_price': self.booking_id.company_booking_price,
                'etd_sale': self.booking_id.voyage_id.etd,
            })

        self.update_done_task()
        self.send_notification_by_stage('done')
        self.message_post(body=_("Approve price successfully with sale line: %s") % self.sale_line_id.name)
        return True
    
    def action_approve_booking(self):
        self.ensure_one()
        self.validate_action_submit('action_approve_booking')

        if not self.sale_order_id or not self.sale_line_id or not self.booking_id:
            raise ValidationError(_("Sales Order, Sales Order Line, and Booking are required."))

            # Add this sale order to the booking's sale_order_ids if not already there
        if self.sale_line_id.id not in self.booking_id.sale_line_ids.ids:
            self.booking_id.sudo().write({
                'sale_line_ids': [(4, self.sale_line_id.id)],
                'booking_status': 'booked',  # Update booking status to booked
            })

        # self.sale_line_id.sudo().write({
        #     'booking_id': self.booking_id.id,
        # })
        self.update_done_task()
        self.send_notification_by_stage('done')
        # self.message_post(body=_("Approve booking success with booking no: %s") % self.booking_id.booking_no)
        # Post a message in the chatter
        self.message_post(body=_(
            "Booking approved successfully. The booking %s has been assigned to %s and linked to the sales order %s."
        ) % (self.booking_id.booking_no, self.sale_line_id.name, self.sale_order_id.name))

        return True
    
    def validate_action_submit(self, action):
        match action:
            case 'action_approve_booking':
                if not self.sale_order_id:
                    raise ValidationError(_("Quotation is required."))
                # if not self.sale_line_id:
                #     raise ValidationError(_("Sale order line is required."))
                if not self.booking_id:
                    raise ValidationError(_("Booking is required."))
                
            case 'action_approve_pod_pol':
                if not self.sale_order_id:
                    raise ValidationError(_("Quotation is required."))
                if not self.pod_name_request:
                    raise ValidationError(_("POD name is required."))
                if not self.pol_name_request:
                    raise ValidationError(_("POL name is required."))
                if not self.region_id:
                    raise ValidationError(_("Region name is required."))
                
            case 'action_approve_price':
                # if not self.product_template_id:
                #     raise ValidationError(_("Product is required."))
                if not self.booking_id:
                    raise ValidationError(_("Booking is required."))
                # if not self.sale_price or not self.cost:
                #     raise ValidationError(_("Sale price or Cost is not exist."))

            # case 'action_confirm_quotation':
            #     if not self.sale_order_id:
            #         raise ValidationError(_("Quotation is not exist."))

            case _:
                return
    
    def send_notification_by_stage(self, stage, assignees_ids=None):
        self.ensure_one()
        activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
        model_id = self.env['ir.model']._get_id('project.task')

        match stage:
            case 'done':
                creator = self.create_uid
                if creator:
                    self.env['mail.activity'].create({
                        'activity_type_id': activity_type_id,
                        'note': f'<p>Task "{self.name}" has been completed.</p>',
                        'res_id': self.id,
                        'res_model_id': model_id,
                        'user_id': creator.id,
                        'summary': f'Task "{self.name}" has been completed.'
                    })
        
            case 'open':
                # assignees = self.user_ids
                if assignees_ids:
                    for assignee_id in assignees_ids:
                        self.env['mail.activity'].create({
                            'activity_type_id': activity_type_id,
                            'note': f'<p>Task "{self.name}" has been assigned to you.</p>',
                            'res_id': self.id,
                            'res_model_id': model_id,
                            'user_id': assignee_id,
                            'summary': f'You have been assigned task "{self.name}".'
                        })

            case _:
                return
