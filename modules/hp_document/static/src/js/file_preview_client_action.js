odoo.define('@hp_document/js/file_preview_client_action', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;

    var FilePreviewClientAction = AbstractAction.extend({
        template: 'hp_document_file_preview_modal',
        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.file_url = action.params.file_url;
            this.mimetype = action.params.mimetype;
            this.name = action.params.name;
        },
        start: function() {
            this.$('.o_file_preview_modal_title').text(this.name);
            if (this.mimetype.startsWith('image/')) {
                this.$('.o_file_preview_content').html('<img src="' + this.file_url + '" style="max-width:100%;max-height:70vh;"/>');
            } else if (this.mimetype === 'application/pdf') {
                this.$('.o_file_preview_content').html('<iframe src="' + this.file_url + '" style="width:100%;height:70vh;" frameborder="0"></iframe>');
            } else if (this.mimetype.startsWith('text/')) {
                this.$('.o_file_preview_content').html('<iframe src="' + this.file_url + '" style="width:100%;height:70vh;" frameborder="0"></iframe>');
            } else {
                this.$('.o_file_preview_content').html('<a href="' + this.file_url + '" target="_blank">Download and open file</a>');
            }
            return this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('hp_document_file_preview', FilePreviewClientAction);

    return FilePreviewClientAction;
}); 