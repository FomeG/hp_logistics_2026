/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

// Define the product models we want to hide the delete button for
const PRODUCT_MODELS = ['pricing.booking', 'pricing.voyage', 'pricing.pod', 'pricing.pol', 'pricing.region', 'pricing.sealine', 'pricing.shipping.line', 'pricing.shipping.vessel', 'pricing.team', 'pricing.team.member'];

patch(ListController.prototype, {
    /**
     * @override
     */
    getStaticActionMenuItems() {
        // Get the original actions
        const actions = super.getStaticActionMenuItems();

        // If we're in a product model, remove the delete action
        if (PRODUCT_MODELS.includes(this.props.resModel)) {
            delete actions.delete;
            delete actions.export;
            delete actions.duplicate;
        }

        return actions;
    },
});