/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";

class Many2OneOpenInNewTab extends Many2OneField {
    async openAction() {
        if (!this.resId) return;
        const context = this.context;
        const model = this.relation;
        const id = this.resId;
        const url = `/web#id=${id}&model=${model}&view_type=form`;
        window.open(url, "_blank");
    }
}

export const many2oneOpenInNewTab = {
    ...registry.category("fields").get("many2one"),
    component: Many2OneOpenInNewTab,
};

registry.category("fields").add("many2one_new_tab", many2oneOpenInNewTab);
