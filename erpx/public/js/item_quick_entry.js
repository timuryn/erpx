frappe.provide("frappe.ui.form");

frappe.ui.form.ItemQuickEntryForm = class ItemQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
    }

    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
        // Force uncheck after render
        this.dialog.set_value("is_stock_item", 0);
    }

    insert() {
        return super.insert().then((response) => {
            if (cur_list && cur_list.doctype === "Item") {
                cur_list.refresh();
            }
            if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Item") {
                frappe.set_route("List", "Item");
            }
            if (cur_frm && cur_frm.fields_dict) {
                Object.keys(cur_frm.fields_dict).forEach(fieldname => {
                    const field = cur_frm.fields_dict[fieldname];
                    if (field && field.df && field.df.options === "Item") {
                        field.refresh();
                    }
                });
            }
            frappe.ui.form.trigger_refresh_field_group && frappe.ui.form.trigger_refresh_field_group();
            return response;
        });
    }

    get_field() {
        return [
            {
                fieldtype: "Section Break",
                label: __("Neu Artikel"),
            },
            {
                label: __("Artikel-Code"),
                fieldname: "item_code",
                fieldtype: "Data",
                reqd: true,
            },
            {
                label: __("Artikelgruppe"),
                fieldname: "item_group",
                fieldtype: "Link",
                options: "Item Group",
            },
            {
                label: __("Standardmaßeinheit"),
                fieldname: "stock_uom",
                fieldtype: "Link",
                options: "UOM",
            },
            {
                label: __("Lager verwalten"),
                fieldname: "is_stock_item",
                fieldtype: "Check",
                default: 0,
            },
            {
                label: __("Beschreibung"),
                fieldname: "description",
                fieldtype: "Text",
            },
            {
                label: __("Standard-Verkaufspreis"),
                fieldname: "standard_rate",
                fieldtype: "Currency",
                default: 0,
            },
        ];
    }
};
