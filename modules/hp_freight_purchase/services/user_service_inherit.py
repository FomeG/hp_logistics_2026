from odoo import models, api

class FreightPurchaseUserService(models.AbstractModel):
    _name = 'hp_freight_purchase.user.service'
    _inherit = 'hp_components.user.service'
    _description = 'Freight Purchase User Service'

    @api.model
    def is_freight_purchase_member(self, user_id=None):
        return self._check_user_has_group('hp_freight_purchase.group_hp_freight_purchase_member', user_id)

    @api.model
    def is_freight_purchase_lead(self, user_id=None):
        return self._check_user_has_group('hp_freight_purchase.group_hp_freight_purchase_lead', user_id)

    @api.model
    def is_freight_purchase_director(self, user_id=None):
        return self._check_user_has_group('hp_freight_purchase.group_hp_freight_purchase_director', user_id)

    @api.model
    def is_freight_purchase_administrator(self, user_id=None):
        return self._check_user_has_group('hp_freight_purchase.group_hp_freight_purchase_administrator', user_id)

    # Permission checks
    @api.model
    def can_edit_region_employees(self, user_id=None):
        """Check if the given user (or current user) can edit region employees. Returns True if user is a Freight Purchase Lead, Director, or Administrator."""
        return (self.is_freight_purchase_lead(user_id) or
                self.is_freight_purchase_director(user_id) or
                self.is_freight_purchase_administrator(user_id))
