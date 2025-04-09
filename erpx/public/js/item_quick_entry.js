frappe.provide("frappe.ui.form");

frappe.ui.form.ItemQuickEntryForm = class ItemQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
    }

    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
    }

    // Ensure correct mapping for fields like item_code, item_group, etc.
    insert() {
        // You can add any additional field mappings or checks here if needed
        return super.insert();
    }

    // Define the fields in the quick entry form
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
                reqd: true,  // Make this field required
            },
            {
                label: __("Artikelgruppe"),
                fieldname: "item_group",
                fieldtype: "Link",
                options: "Item Group",  // Link to the Item Group doctype
            },
            {
                label: __("Standardmaßeinheit"),
                fieldname: "stock_uom",
                fieldtype: "Link",
                options: "UOM",  // Link to the Unit of Measure doctype
            },
            {
                label: __("Lager verwalten"),
                fieldname: "is_stock_item",
                fieldtype: "Check",
                default: 1,  // Precheck this checkbox by default
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
                default: 0,  // Default value can be set to 0
            },
        ];
    }
};

