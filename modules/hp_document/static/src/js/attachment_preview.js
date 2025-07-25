/** @odoo-module **/
import {registry} from "@web/core/registry";
import {Component, useState} from "@odoo/owl";
import {FileInput} from "@web/core/file_input/file_input";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";
import {useX2ManyCrud} from "@web/views/fields/relational_utils";

/**
 * The HPDocumentAttachmentPreview component is designed to manage the preview and handling
 * of attachment files in the hp_document module. It allows users to view and download files
 * with a modern UI using Fancybox for previews.
 */
export class HPDocumentAttachmentPreview extends Component {
    static template = 'hp_document.AttachmentPreview'
    static components = {
        FileInput,
    };
    static props = {
        ...standardFieldProps,
        acceptedFileExtensions: {type: String, optional: true},
        className: {type: String, optional: true},
        numberOfFiles: {type: Number, optional: true},
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.operations = useX2ManyCrud(() => this.props.value, true);
        this.state = useState({
            flag: false,
        });
    }

    get uploadText() {
        return this.props.record.fields[this.props.name].string;
    }

    get files() {
        return this.props.record.data[this.props.name].records.map((record) => {
            return {
                ...record.data,
                id: record.resId,
            };
        });
    }

    getUrl(id) {
        return "/web/content/ir.attachment/" + id + "/datas";
    }

    getExtension(file) {
        return file.name.replace(/^.*\./, "");
    }

    async onFileUploaded(files) {
        for (const file of files) {
            if (file.error) {
                return this.notification.add(file.error, {
                    title: this.env._t("Uploading error"),
                    type: "danger",
                });
            }
            await this.operations.saveRecord([file.id]);
        }
    }

    async onFileRemove(deleteId) {
        const record = this.props.value.records.find((record) => record.data.id === deleteId);
        this.operations.removeRecord(record);
    }
}

HPDocumentAttachmentPreview.supportedTypes = ["many2many"];
HPDocumentAttachmentPreview.fieldsToFetch = {
    name: {
        type: 'char'
    },
    mimetype: {
        type: 'char'
    },
}
registry.category("fields").add("hp_document_attachment_preview", HPDocumentAttachmentPreview) 