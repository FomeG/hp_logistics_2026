/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

// Define the product models we want to hide the property button for
const PRODUCT_MODELS = ['product.template', 'product.product'];

patch(FormController.prototype, {
    /**
     * @override
     */
    getStaticActionMenuItems() {
        // Get the original menu items
        const menuItems = super.getStaticActionMenuItems();

        // If we're in a product model, remove the addPropertyFieldValue option
        if (PRODUCT_MODELS.includes(this.props.resModel)) {
            delete menuItems.addPropertyFieldValue;
        }

        return menuItems;
    },
});