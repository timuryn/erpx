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
    
    // Ensure correct mapping for fields like item_code, item_group, etc. with auto-refresh
    insert() {
        // You can add any additional field mappings or checks here if needed
        
        // Call parent insert method and handle the response
        return super.insert().then((response) => {
            // Multiple approaches to refresh the list/views
            
            // Method 1: Try cur_list first
            if (cur_list && cur_list.doctype === "Item") {
                cur_list.refresh();
            }
            
            // Method 2: Try to find list view in current page
            if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Item") {
                frappe.set_route("List", "Item");
            }
            
            // Method 3: Refresh item link fields
            if (cur_frm && cur_frm.fields_dict) {
                Object.keys(cur_frm.fields_dict).forEach(fieldname => {
                    const field = cur_frm.fields_dict[fieldname];
                    if (field && field.df && field.df.options === "Item") {
                        field.refresh();
                    }
                });
            }
            
            // Method 4: Trigger a global refresh event
            frappe.ui.form.trigger_refresh_field_group && frappe.ui.form.trigger_refresh_field_group();
            
            return response;
        });
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
