/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component } from "@odoo/owl";

export class DateTagsField extends Component {
    static template = "hp_sale.DateTagsField";
    static props = {
        ...standardFieldProps,
    };

    get dates() {
        const value = this.props.record.data[this.props.name];
        if (!value) return [];
        try {
            const dates = JSON.parse(value);
            return Array.isArray(dates) ? dates : [];
        } catch {
            return [];
        }
    }

    get isReadonly() {
        return this.props.readonly;
    }

    removeDate(dateToRemove) {
        if (this.isReadonly) return;

        const currentDates = this.dates;
        const newDates = currentDates.filter(d => d !== dateToRemove);
        const newValue = newDates.length > 0 ? JSON.stringify(newDates) : false;

        this.props.record.update({ [this.props.name]: newValue });
    }

    formatDate(dateStr) {
        return dateStr;
    }
}

export const dateTagsField = {
    component: DateTagsField,
    supportedTypes: ["char", "text"],
};

registry.category("fields").add("date_tags", dateTagsField);
