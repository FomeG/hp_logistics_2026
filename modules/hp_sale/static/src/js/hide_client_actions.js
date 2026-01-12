/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";

// Add res.partner.client to the models we want to control
const MODELS = ['res.partner.client'];

const ALLOWED_GROUPS = [
    'sales_team.group_sale_salesman_all_leads',
    'sales_team.group_sale_manager',
    'base.group_system',
];

const getPatch = () => ({
    setup() {
        super.setup();
        
        onWillStart(async () => {
            this._canSeeClientActions = false;
            // Check if user has any of the allowed groups (Leader/Manager/Admin)
            for (const group of ALLOWED_GROUPS) {
                if (await user.hasGroup(group)) {
                    this._canSeeClientActions = true;
                    break;
                }
            }
        });
    },

    getStaticActionMenuItems() {
        const menuItems = super.getStaticActionMenuItems();
        
        // If we're in a target model and user is only a salesman
        if (MODELS.includes(this.props.resModel) && !this._canSeeClientActions) {
            // Remove archive/unarchive
            delete menuItems.archive;
            delete menuItems.unarchive;
            // Remove duplicate
            delete menuItems.duplicate;
        }
        
        return menuItems;
    }
});

patch(FormController.prototype, getPatch());
patch(ListController.prototype, getPatch());
