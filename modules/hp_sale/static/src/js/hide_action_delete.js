/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { patch } from "@web/core/utils/patch";

// Define the product models we want to hide the delete button for
const PRODUCT_MODELS = ['product.template', 'product.product'];

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
        }

        return actions;
    },
});