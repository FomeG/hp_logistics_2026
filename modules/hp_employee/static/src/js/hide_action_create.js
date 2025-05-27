
/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

patch(ListController.prototype, {
    /**
     * @override
     */
    async setup() {
        super.setup();

        this.orm = useService("orm");

        onMounted(async () => {
            const canCreate = await this.orm.call(
                "hr.department",
                "can_create_department"
            );

            if (!canCreate) {
                const btn = document.querySelector(".o_list_button_add");
                if (btn) btn.style.display = "none";
            }
        });
    },
});

patch(FormController.prototype, {
    /**
     * @override
     */
    async setup() {
        super.setup();

        this.orm = useService("orm");

        onMounted(async () => {
            const canCreate = await this.orm.call(
                "hr.department",
                "can_create_department"
            );

            if (!canCreate) {
                const btn = document.querySelector(".o_form_button_create");
                if (btn) btn.style.display = "none";
            }
        });
    },
});

patch(KanbanController.prototype, {
    /**
     * @override
     */
    async setup() {
        super.setup();

        this.orm = useService("orm");

        onMounted(async () => {
            const canCreate = await this.orm.call(
                "hr.department",
                "can_create_department"
            );

            if (!canCreate) {
                const btn = document.querySelector(".o-kanban-button-new");
                if (btn) btn.style.display = "none";
            }
        });
    },
});

// patch(HierarchyController.prototype, {
//     /**
//      * @override
//      */
//     async setup() {
//         super.setup();

//         this.orm = useService("orm");

//         onMounted(async () => {
//             const canCreate = await this.orm.call(
//                 "hr.department",
//                 "can_create_department"
//             );

//             if (!canCreate) {
//                 const btn = document.querySelector(".o_hierarchy_button_add");
//                 if (btn) btn.style.display = "none";
//             }
//         });
//     },
// });