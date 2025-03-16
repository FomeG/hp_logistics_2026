from odoo import models, api
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        valid_vals = []
        duplicate_vats = []
        for vals in vals_list:
            vat = vals.get('vat')
            if vat:
                existing_partner = self.env['res.partner'].search([('vat', '=', vat)], limit=1)
                if existing_partner:
                    duplicate_vats.append(vat)
                    continue
            valid_vals.append(vals)

        created_records = self.env['res.partner'].browse()
        if valid_vals:
            created_records = super().create(valid_vals)
            self.env.cr.commit()

        if duplicate_vats:
            message = "Tax ID is exist: %s" % ", ".join(duplicate_vats)
            raise UserError(message)

        return created_records
    
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'user_id' in fields and not res.get('user_id'):
            res['user_id'] = self.env.uid

        return res
    
    @api.constrains('vat', 'phone', 'customer_rank')
    def _check_required_fields(self):
        if self.env.context.get('params'):
            for record in self:
                if record.customer_rank > 0:
                    if not record.vat:
                        raise ValidationError("Tax ID is required!")
                    if not record.phone:
                        raise ValidationError("Phone is required!")

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.is_only_group_sale_salesman():
            self.user_id = self._origin.user_id
            raise UserError('Can not change saleperson')
    
    def _get_sale_domain(self):
        current_user_id = self.env.uid
        current_partner_id = self.env.user.partner_id.id or 0

        return ['|', ('user_id', '=', current_user_id), ('id', '=', current_partner_id)]
    
    def is_only_group_sale_salesman(self):
        group_sale_salesman_id = self.env.ref('sales_team.group_sale_salesman').id
        group_sale_salesman_all_leads_id = self.env.ref('sales_team.group_sale_salesman_all_leads').id
        group_sale_manager_id = self.env.ref('sales_team.group_sale_manager').id
        user_group_ids = self.env.user.groups_id.ids

        return (
            group_sale_salesman_id in user_group_ids and 
            group_sale_salesman_all_leads_id not in user_group_ids and 
            group_sale_manager_id not in user_group_ids
        )
    
    @api.model
    @api.readonly
    @api.returns('self')
    def search(self, args, offset=0, limit=None, order=None):
        if self.is_only_group_sale_salesman():
            args = expression.AND([args, self._get_sale_domain()])

        return super().search(args, offset=offset, limit=limit, order=order)

    @api.model
    @api.readonly
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if self.is_only_group_sale_salesman():
            args = expression.AND([args, self._get_sale_domain()])

        return super().name_search(name, args=args, operator=operator, limit=limit)
    
    @api.model
    @api.readonly
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.is_only_group_sale_salesman():
            args = expression.AND([args, self._get_sale_domain()])
        
        return super().read_group(
            domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy
        )
    
    @api.model
    @api.readonly
    def search_read(self, domain, fields=None, offset=0, limit=None, order=None):
        if self.is_only_group_sale_salesman():
            domain = expression.AND([domain, self._get_sale_domain()])

        return super().search_read(domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    @api.readonly
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        if self.is_only_group_sale_salesman():
            domain = expression.AND([domain, self._get_sale_domain()])

        return super().web_search_read(domain, specification=specification, offset=offset, limit=limit, order=order, count_limit=count_limit)