frappe.provide("frappe.ui.form");

frappe.ui.form.SupplierQuickEntryForm = class SupplierQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
    }
    
    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
    }
    
    // Handle field mapping for supplier-specific fields and auto-refresh
    insert() {
        const map_field_names = {
            email_address: "email_id",
            mobile_number: "mobile_no",
        };
        
        Object.entries(map_field_names).forEach(([fieldname, new_fieldname]) => {
            if (this.dialog.doc[fieldname]) {
                this.dialog.doc[new_fieldname] = this.dialog.doc[fieldname];
                delete this.dialog.doc[fieldname];
            }
        });
        
        // Call parent insert method and handle the response
        return super.insert().then((response) => {
            // Refresh the list view if we're on a list page
            if (cur_list && cur_list.doctype === "Supplier") {
                cur_list.refresh();
            }
            
            // Also refresh any open forms that might have supplier links
            if (cur_frm && cur_frm.fields_dict) {
                Object.keys(cur_frm.fields_dict).forEach(fieldname => {
                    const field = cur_frm.fields_dict[fieldname];
                    if (field && field.df && field.df.options === "Supplier") {
                        field.refresh();
                    }
                });
            }
            
            return response;
        });
    }
    
    // Define the fields in the quick entry form
    get_field() {
        return [
            {
                fieldtype: "Section Break",
                label: __("Lieferant"),
            },
            {
                label: __("Lieferant"),
                fieldname: "supplier_name",
                fieldtype: "Data",
                reqd: 1,
            },
            {
                label: __("Lieferantengruppe"),
                fieldname: "supplier_group",
                fieldtype: "Link",
                options: "Supplier Group",
                reqd: 1,
            },
            {
                label: __("Lieferantendetails"),
                fieldname: "supplier_details",
                fieldtype: "Text",
            },
            {
                fieldtype: "Section Break",
                label: __("Kontakt"),
            },
            {
                label: __("Vorname"),
                fieldname: "first_name",
                fieldtype: "Data",
            },
            {
                label: __("Mobilfunknummer"),
                fieldname: "mobile_number",
                fieldtype: "Data",
            },
            {
                label: __("Webseite"),
                fieldname: "website",
                fieldtype: "Data",
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __("Nachname"),
                fieldname: "last_name",
                fieldtype: "Data",
            },
            {
                label: __("E-Mail-Adresse"),
                fieldname: "email_address",
                fieldtype: "Data",
                options: "Email",
            },
            {
                fieldtype: "Section Break",
                label: __("Adresse"),
            },
            {
                label: __("Straße"),
                fieldname: "address_line1",
                fieldtype: "Data",
            },
            {
                label: __("Postleitzahl"),
                fieldname: "pincode",
                fieldtype: "Data",
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __("Ort"),
                fieldname: "city",
                fieldtype: "Data",
            },
            {
                label: __("Land"),
                fieldname: "country",
                fieldtype: "Link",
                options: "Country",
                default: "Germany",
            },
        ];
    }
};
