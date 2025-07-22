from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import logging
from odoo.addons.hp_components.services.task_service import TaskService
from odoo.addons.hp_components.services.project_service import ProjectService

_logger = logging.getLogger(__name__)

class ProjectTaskInherit(models.Model):
    _inherit = 'project.task'

    start_time = fields.Datetime(string="Start Time", readonly=True)
    end_time = fields.Datetime(string="End Time", readonly=True)

    # Request POD/POL
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', store=True)
    pod_name_request = fields.Char('POD name request')
    pod_id = fields.Many2one('freight.purchase.port', string="Port Of Discharge")
    pol_name_request = fields.Char('POL name request')
    pol_id = fields.Many2one('freight.purchase.port', string="Port Of Loading")
    region_pol_id = fields.Many2one('freight.purchase.region', string='Region POL')
    region_pod_id = fields.Many2one('freight.purchase.region', string='Region POD')
    container_type_id = fields.Many2one('container.type', string='Container Type (For this quotation)')

    # Request price product
    quotation_id = fields.Many2one('freight.purchase.quotation', string='Pricing Quotation')
    booking_id = fields.Many2one('freight.purchase.booking', string='Booking')
    etd = fields.Date(string="Estimated time of departure")
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)
    cost = fields.Monetary(string="Cost", currency_field='currency_id')

    # Asign booking
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Line')

    # Approve quotation
    rejection_reason = fields.Text(string='Rejection Reason')

    # Computed
    project_type = fields.Char(string="Project Type", compute="_compute_project_type", store=False)
    product_template_id = fields.Many2one('product.template', string='Product', compute='_compute_product_template_id', store=False)
    is_quotation = fields.Boolean(compute='_compute_state_sale_order', store=False)
    is_project_pricing = fields.Boolean(compute="_check_project_pricing", store=False)
    is_done = fields.Boolean(string="Is Done", compute="_compute_is_done", store=False)
    allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_user_ids', store=False)

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
    def _compute_allowed_user_ids(self):
        for task in self:
            if task.project_id:
                sale_group_id = self.env.ref('sales_team.group_sale_salesman').id
                freight_purchase_group_id = self.env.ref('hp_freight_purchase.group_hp_freight_purchase_member').id

                type = task.project_id.type
                if type == 'approve_quotation':
                    domain = [('groups_id', 'in', [sale_group_id, freight_purchase_group_id])]
                elif type in ('request_product', 'request_price', 'assign_booking'):
                    domain = [('groups_id', 'in', [freight_purchase_group_id])]
                else:
                    domain = [('active', '=', True), ('share', '=', False)]

            users = self.env['res.users'].sudo().search(domain)
            task.allowed_user_ids = users

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
                if task.sale_line_id.product_id.type not in ['pricing', 'trucking', 'common', 'custom'] or task.sale_line_id.is_expense:
                    raise ValidationError(_(
                        'You cannot link the order item %(order_id)s - %(product_id)s to this task because it is a re-invoiced expense.',
                        order_id=task.sale_line_id.order_id.name,
                        product_id=task.sale_line_id.product_id.display_name,
                    ))

    @api.depends('sale_line_id')
    def _compute_product_template_id(self):
        for task in self:
            sale_order_line = task.sale_line_id
            if sale_order_line and sale_order_line.product_template_id:
                task.product_template_id = sale_order_line.product_template_id.id
            else:
                task.product_template_id = False

    @api.depends('project_id')
    def _check_project_pricing(self):
        for task in self:
            task.is_project_pricing = True if task.project_id.type in task.project_id.PROTECTED_TYPE else False

    @api.depends('project_id', 'project_id.type')
    def _compute_project_type(self):
        for task in self:
            task.project_type = task.project_id.type if task.project_id else False

    @api.depends('sale_order_id')
    def _compute_state_sale_order(self):
        for task in self:
            task.is_quotation = True if task.sale_order_id.state == 'draft' else False

    @api.onchange('etd')
    def _onchange_etd_set_booking_domain(self):
        if self.etd:
            return {
                'domain': {
                    'booking_id': [('etd', '>=', self.etd)]
                }
            }

    @api.onchange('booking_id')
    def _onchange_booking_id(self):
       self.etd = self.booking_id.etd

    # Update done task
    def update_done_task(self, pod_id = None, pol_id = None):
        done_stage = self.env['project.task.type'].search([('name', '=', 'Done')], limit=1)
        self.write({
            'stage_id': done_stage.id if done_stage else self.stage_id.id,
            'pod_id': pod_id,
            'pol_id': pol_id,
        })
        return True

    # Avoiding order to be confirmed from project/task
    def _ensure_sale_order_linked(self, sol_ids):
        if self.env.context.get('skip_so_confirmation'):
            return
        return super()._ensure_sale_order_linked(sol_ids)

    # ====== start action show form ======
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

    def action_pricing_quotation_detail(self):
        self.ensure_one()
        return {
            'name': _('Pricing Quotation Detail'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.quotation',
            'view_mode': 'form',
            'res_id': self.quotation_id.id,
            'target': 'new',
            'context': {'create': False, 'update': False, 'delete': False},
            'flags': {'mode': 'readonly'},
        }

    def action_create_pricing_quotation(self):
        self.ensure_one()
        return {
            'name': _('Create Pricing Quotation'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.quotation',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_freight_purchase.freight_purchase_quotation_form_view').id,
            'target': 'new',
            'context': dict(self._context, **{
                'default_project_task_id': self.id,
                'default_route_id': self.product_template_id.route_id.id,
                'default_container_type_id': self.container_type_id.id,
            })
        }

    def action_create_pricing_booking(self):
        self.ensure_one()
        return {
            'name': _('Create Pricing Booking'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.booking',
            'view_mode': 'form',
            'view_id': self.env.ref('hp_freight_purchase.freight_purchase_booking_form_view').id,
            'target': 'new',
            'context': dict(self._context, **{
                'default_project_task_id': self.id,
                'default_quotation_id': self.quotation_id.id,
            })
        }

    def action_show_pricing_booking(self):
        self.ensure_one()
        return {
            'name': _('Pricing Booking Detail'),
            'type': 'ir.actions.act_window',
            'res_model': 'freight.purchase.booking',
            'view_mode': 'form',
            'res_id': self.booking_id.id,
            'target': 'new',
            'context': {'create': False, 'update': False, 'delete': False},
            'flags': {'mode': 'readonly'},
        }
    # ====== end action show form ======

    # ====== start action approve reject ======
    # 1. create sale order line by pol, pod
    def action_approve_pod_pol(self):
        self.ensure_one()
        task_service = TaskService(self.env)
        result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_APPROVE_POL_POL)
        if (result):
            self.message_post(body=_("Create POD/POL successfully: %s, %s") % (self.pod_name_request, self.pol_name_request))
            return True
        raise UserError('Create POD/POL failed.')

    # 2. Approve price to sale order line
    def action_approve_price(self):
        self.ensure_one()
        task_service = TaskService(self.env)
        result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_APPROVE_PRICE)
        if (result):
            self.message_post(body=_("Approve price successfully with sale line: %s") % self.sale_line_id.name)
            return True
        raise UserError('Approve price failed.')
    
    # 3. sale leader approve/reject
    def action_sale_leader_approve(self):
        self.ensure_one()
        task_service = TaskService(self.env)
        result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_APPROVE_QUOTATION_BY_SALE)
        if (result):
            self.message_post(body=_("Quotation approved by sales leader."))
            return True
        raise UserError('Approve quotation failed.')

    def action_sale_leader_reject(self):
        self.ensure_one()
        task_service = TaskService(self.env)
        result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_REJECT_QUOTATION_BY_SALE)
        if (result):
            self.message_post(body=_("Quotation rejected by sales leader and set back to Activated state. Reason: %s") % self.rejection_reason)
            return True
        raise UserError('Reject quotation failed.')

    # 4. pricing leader assign booking to sale order line
    def action_pricing_assign_booking(self):
        self.ensure_one()
        task_service = TaskService(self.env)
        result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_ASSIGN_BOOKING)
        if (result):
            self.message_post(body=_(
                "Booking approved successfully. The booking %s has been assigned to %s and linked to the sales order %s."
            ) % (self.booking_id.name, self.sale_line_id.name, self.sale_order_id.name))
            return True
        raise UserError('Approve booking failed.')
    
    # def action_pricing_reject(self):
    #     self.ensure_one()
    #     task_service = TaskService(self.env)
    #     result = task_service.handle_by_action(self, ProjectService(self.env).ACTION_REJECT_QUOTATION_BY_PRICING)
    #     if (result):
    #         self.message_post(body=_("Quotation rejected by pricing leader. Reason: %s") % self.rejection_reason)
    #         return True
    #     raise UserError('Reject quotation failed.')
    # ====== end action approve reject ======

    def sale_order(self):
        self.ensure_one()
        return self.sale_order_id or (self.sale_line_id and self.sale_line_id.sale_order_id)