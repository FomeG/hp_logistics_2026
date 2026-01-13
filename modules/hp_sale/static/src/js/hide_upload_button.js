/** @odoo-module **/

import { FileUploadListController } from "@account/views/file_upload_list/file_upload_list_controller";
import { FileUploadKanbanController } from "@account/views/file_upload_kanban/file_upload_kanban_controller";
import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";
import { onWillStart } from "@odoo/owl";
const ALLOWED_GROUPS = [
    'sales_team.group_sale_salesman_all_leads',
    'sales_team.group_sale_manager',
    'base.group_system',
];
const getUploadButtonPatch = () => ({
    setup() {
        super.setup();
        this.canUpload = false;
        onWillStart(async () => {
            const groupChecks = ALLOWED_GROUPS.map(group => user.hasGroup(group));
            const results = await Promise.all(groupChecks);
            this.canUpload = results.some(hasGroup => hasGroup);
        });
    },
});
patch(FileUploadListController.prototype, getUploadButtonPatch());
patch(FileUploadKanbanController.prototype, getUploadButtonPatch());