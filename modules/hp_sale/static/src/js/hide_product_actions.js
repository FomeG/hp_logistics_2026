/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

const PRODUCT_MODELS = ['product.template', 'product.product'];

const ALLOWED_GROUPS = [
    'sales_team.group_sale_salesman_all_leads',
    'sales_team.group_sale_manager',
    'base.group_system',
];

/**
 * Patch FormController to hide Archive action for sale members in product forms
 */
patch(FormController.prototype, {
    setup() {
        super.setup();
        
        onWillStart(async () => {
            // Check if user has any of the allowed groups
            this._canSeeProductActions = false;
            for (const group of ALLOWED_GROUPS) {
                if (await user.hasGroup(group)) {
                    this._canSeeProductActions = true;
                    break;
                }
            }
        });
    },

    /**
     * @override
     */
    getStaticActionMenuItems() {
        const menuItems = super.getStaticActionMenuItems();
        
        // If we're in a product model and user is a salesman (not DOS/Manager/Admin)
        if (PRODUCT_MODELS.includes(this.props.resModel) && !this._canSeeProductActions) {
            // Remove archive and unarchive actions
            delete menuItems.archive;
            delete menuItems.unarchive;
        }
        
        return menuItems;
    },

    /**
     * @override
     * Filter out Pricelist Report from action menu items for sale members
     */
    get actionMenuItems() {
        const items = super.actionMenuItems;
        
        // If we're in a product model and user is a salesman (not DOS/Manager/Admin)
        if (PRODUCT_MODELS.includes(this.props.resModel) && !this._canSeeProductActions) {
            // Filter out Pricelist Report from action items
            if (items.action) {
                items.action = items.action.filter(
                    item => !item.name?.toLowerCase().includes('pricelist')
                );
            }
        }
        
        return items;
    },
});

/**
 * Patch ListController to hide Archive action for sale members in product lists
 */
patch(ListController.prototype, {
    setup() {
        super.setup();
        
        onWillStart(async () => {
            // Check if user has any of the allowed groups
            this._canSeeProductActions = false;
            for (const group of ALLOWED_GROUPS) {
                if (await user.hasGroup(group)) {
                    this._canSeeProductActions = true;
                    break;
                }
            }
        });
    },

    /**
     * @override
     */
    getStaticActionMenuItems() {
        const menuItems = super.getStaticActionMenuItems();
        
        // If we're in a product model and user is a salesman (not DOS/Manager/Admin)
        if (PRODUCT_MODELS.includes(this.props.resModel) && !this._canSeeProductActions) {
            // Remove archive and unarchive actions
            delete menuItems.archive;
            delete menuItems.unarchive;
        }
        
        return menuItems;
    },

    /**
     * @override
     * Filter out Pricelist Report from action menu items for sale members
     */
    get actionMenuItems() {
        const items = super.actionMenuItems;
        
        // If we're in a product model and user is a salesman (not DOS/Manager/Admin)
        if (PRODUCT_MODELS.includes(this.props.resModel) && !this._canSeeProductActions) {
            // Filter out Pricelist Report from action items
            if (items.action) {
                items.action = items.action.filter(
                    item => !item.name?.toLowerCase().includes('pricelist')
                );
            }
        }
        
        return items;
    },
});
