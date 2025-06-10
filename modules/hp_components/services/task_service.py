from .cancel_task_service import CancelTaskService
from .price_request_service import PriceRequestService
from .approve_quotation_service import ApproveQuotationService
from .product_request_service import ProductRequestService
from .sale_order_service import SaleOrderService
from .department_service import DepartmentService
from odoo.exceptions import ValidationError, UserError
from odoo import _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class TaskService:
    _name = 'task.service'
    TASK_TYPE_PRICE_REQUEST = 'price_request'
    TASK_TYPE_APPROVE_QUOTATION = 'approve_quotation'
    TASK_TYPE_PRODUCT_REQUEST = 'product_request'
    PROJECT_TYPE_PRICE_REQUEST = 'request_price'
    PROJECT_TYPE_APPROVE_QUOTATION = 'approve_quotation'
    PROJECT_TYPE_PRODUCT_REQUEST = 'request_product'

    ACTION_APPROVE_POL_POL = 'approve_pod_pol'
    ACTION_APPROVE_PRICE = 'approve_price'
    ACTION_APPROVE_BOOKING = 'approve_booking'
    ACTION_REJECT_QUOTATION_BY_PRICING = 'reject_quotation_by_pricing'
    ACTION_REJECT_QUOTATION_BY_SALE = 'reject_quotation_by_sale'
    ACTION_APPROVE_QUOTATION_BY_PRICING = 'approve_quotation_by_pricing'
    ACTION_APPROVE_QUOTATION_BY_SALE = 'approve_quotation_by_sale'

    SALE_TYPE = 'sale'
    PRICING_TYPE = 'pricing'

    def __init__(self, env):
        self.env = env

    def create_task_by_sale_order_line(self, project_id, task_type, sale_order_line):
        if task_type == self.TASK_TYPE_PRICE_REQUEST:
            PriceRequestService(self.env).create(project_id, sale_order_line)

    def create_task_by_sale_order(self, department_type, project_id, task_type, sale_order, etd=False, pod_name_request=False, pol_name_request=False, volume_cont=False):
        if task_type == self.TASK_TYPE_APPROVE_QUOTATION:
            ApproveQuotationService(self.env).create(department_type, project_id, sale_order)
        elif task_type == self.TASK_TYPE_PRODUCT_REQUEST:
            ProductRequestService(self.env)._create_product_request_task(project_id, sale_order, etd, pod_name_request, pol_name_request, volume_cont)

    def cancel_tasks_by_sale_order(self, sale_order):
            CancelTaskService(self.env).cancel_tasks_by_sale_order(sale_order)

    def update_sale_order_line_price_by_task(self, task):
        """
        apply on price request project
        """
        price_request_project = self.get_project_by_type(TaskService.PROJECT_TYPE_PRICE_REQUEST)
        if task.project_id.id != price_request_project.id:
            return
        service =  SaleOrderService(self.env)
        #todo: check task has been updated with price
        service.update_sale_order_line_price_by_task(project_task=task)

    def get_project_by_type(self, project_type=''):
        project = self.env['project.project'].search([('type', '=', project_type)], limit=1)
        return project if project else False
    
    def handle_approve_pod_pol(self, record):
        self.validate_by_action(record, self.ACTION_APPROVE_POL_POL)

        pol = self.env['pricing.pol'].search([('pol_name', 'ilike', record.pol_name_request)], limit=1)
        pod = self.env['pricing.pod'].search([('pod_name', 'ilike', record.pod_name_request)], limit=1)
        if not pod:
            pod = self.env['pricing.pod'].create({
                'pod_name': record.pod_name_request,
                'region_id': record.region_id.id,
            })
        if not pol:
            pol = self.env['pricing.pol'].create({
                'pol_name': record.pol_name_request
            })

        new_sealine = self.env['pricing.sealine'].search([('pod_id', '=', pod.id), ('pol_id', '=', pol.id)], limit=1)
        if new_sealine:
            new_product = self.env['product.template'].search([('sealine_id', '=', new_sealine.id)], limit=1)
            if new_product:
                # add sale order item
                sale_order = record.sale_order_id
                new_sale_order_line = self.env['sale.order.line'].sudo().create({
                    'order_id': sale_order.id,
                    'product_id': new_product.product_variant_id.id,
                    'volume_cont': record.volume_cont,
                    'product_uom_qty': 1.0,
                    'name': new_product.name,
                    'product_type_filter': 'pricing'
                })

                # create task request price
                self.create_task_request_price(record, new_product, sale_order, new_sale_order_line)

                sale_order.sudo().write({'state': 'activated'})
                record.update_done_task(pod.id, pol.id)
                return True
        return False
    
    def create_task_request_price(self, task, product, sale_order, sale_order_line):
        project_request_price = self.env['project.project'].search([('type', '=', self.PROJECT_TYPE_PRICE_REQUEST)], limit=1)
        if project_request_price:
            task_vals = {
                'name': product.name,
                'project_id': project_request_price.id,
                'sale_order_id': sale_order.id,
                'sale_line_id': sale_order_line.id,
                'etd': task.etd,
                'date_assign': datetime.now(),
            }

            # Add assignees pricing leader
            pricing_leader = DepartmentService(self.env).get_pricing_department_leader()
            assignee_ids = [pricing_leader.id] if pricing_leader else []
            if assignee_ids:
                task_vals['user_ids'] = [(6, 0, assignee_ids)]

            self.env['project.task'].sudo().with_context(skip_so_confirmation=True).create(task_vals)
            return True
        return False
    
    def handle_approve_price(self, record):
        self.validate_by_action(record, self.ACTION_APPROVE_PRICE)

        # Determine base price based on container type
        cont = record.sale_line_id.volume_cont
        _logger.info(f"cont: {cont}")
        if cont in ['40DC', '40HC', '40HQ', '40RF', '40HCRF', '40OT']:
            multiplier = 2
        elif cont in ['20DC', '20RF', '20OT', '20HC']:
            multiplier = 1
        else:
            raise UserError(_("Unrecognized container type: %s") % cont)

        base_price = (record.booking_id.company_booking_price * multiplier) / record.booking_id.volume_total

        # Find and update the matching sale order line
        if record.sale_line_id:
            record.sale_line_id.sudo().write({
                'booking_id': record.booking_id.id,
                'base_price': base_price,
                'etd_sale': record.booking_id.voyage_id.etd,
            })

        record.update_done_task()
        return True
    
    def handle_approve_booking(self, record):
        self.validate_by_action(record, self.ACTION_APPROVE_BOOKING)

        if record.sale_line_id.id not in record.booking_id.sale_line_ids.ids:
            record.booking_id.sudo().write({
                'sale_line_ids': [(4, record.sale_line_id.id)],
                'booking_status': 'booked',  # Update booking status to booked
            })

        record.update_done_task()
        return True
    
    def handle_reject_quotation_by_type(self, record, type):
        match type:
            case self.SALE_TYPE:
                self.validate_by_action(record, self.ACTION_REJECT_QUOTATION_BY_SALE)
                record.sale_order_id.sudo().write({'state': 'activated'})
            case self.PRICING_TYPE:
                self.validate_by_action(record, self.ACTION_REJECT_QUOTATION_BY_PRICING)
                record.sale_order_id.sudo().write({'state': 'customer_confirm'})
            case _:
                return False

        record.update_done_task()
        return True

    def handle_approve_quotation_by_type(self, record, type):
        match type:
            case self.SALE_TYPE:
                self.validate_by_action(record, self.ACTION_APPROVE_QUOTATION_BY_SALE)
                pricing_lines_without_booking = record.sale_order_id.order_line.filtered(
                    lambda line: line.product_type_filter == 'pricing'
                )
                if not pricing_lines_without_booking:
                    record.sale_order_id.sudo().write({'state': 'sale'})
                else:
                    record.sale_order_id.sudo().action_sale_leader_approved()
        
            case self.PRICING_TYPE:
                self.validate_by_action(record, self.ACTION_APPROVE_QUOTATION_BY_PRICING)
                record.sale_order_id.sudo().action_pricing_leader_approved()
            case _:
                return False
        
        record.update_done_task()
        return True
    
    def validate_by_action(self, record, action):
        match action:
            case self.ACTION_APPROVE_BOOKING:
                if not record.sale_order_id:
                    raise ValidationError(_("Quotation is required."))
                if not record.booking_id:
                    raise ValidationError(_("Booking is required."))
                if not record.sale_line_id:
                    raise ValidationError(_("Sales order line is required."))
                
            case self.ACTION_APPROVE_POL_POL:
                if not record.sale_order_id:
                    raise ValidationError(_("Quotation is required."))
                if not record.pod_name_request:
                    raise ValidationError(_("POD name is required."))
                if not record.pol_name_request:
                    raise ValidationError(_("POL name is required."))
                if not record.region_id:
                    raise ValidationError(_("Region name is required."))
                
            case self.ACTION_APPROVE_PRICE:
                if not record.booking_id:
                    raise ValidationError(_("Booking is required."))
                if not record.pricing_quotation_id:
                    raise ValidationError(_("Pricing quotation is required."))
                if not record.booking_id.volume_total:
                    raise ValidationError(_("Booking has no valid volume total (TEU)."))
                if not record.sale_line_id.volume_cont:
                    raise ValidationError(_("Container type is required when Booking is selected."))
            
            case self.ACTION_REJECT_QUOTATION_BY_PRICING:
                if not record.sale_order_id or record.sale_order_id.state != 'sale_leader_confirm':
                    raise ValidationError(_("This quotation cannot be rejected in its current state."))
                if not record.rejection_reason:
                    raise ValidationError(_("Please provide a reason for rejection."))
            
            case self.ACTION_REJECT_QUOTATION_BY_SALE:
                if not record.sale_order_id or record.sale_order_id.state != 'customer_confirm':
                    raise ValidationError(_("This quotation cannot be rejected in its current state."))

                if not record.rejection_reason:
                    raise ValidationError(_("Please provide a reason for rejection."))
            
            case self.ACTION_APPROVE_QUOTATION_BY_PRICING:
                if not record.sale_order_id or record.sale_order_id.state != 'sale_leader_confirm':
                    raise ValidationError(_("This quotation cannot be approved in its current state."))
            
            case self.ACTION_APPROVE_QUOTATION_BY_SALE:
                if not record.sale_order_id or record.sale_order_id.state != 'customer_confirm':
                    raise ValidationError(_("This quotation cannot be approved in its current state."))

            case _:
                return