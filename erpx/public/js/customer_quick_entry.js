frappe.provide("frappe.ui.form");

frappe.ui.form.CustomerQuickEntryForm = class CustomerQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
    }
    
    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
    }
    
    // Ensure correct mapping for email, phone, and mobile with auto-refresh
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
            // Multiple approaches to refresh the list/views
            
            // Method 1: Try cur_list first
            if (cur_list && cur_list.doctype === "Customer") {
                cur_list.refresh();
            }
            
            // Method 2: Try to find list view in current page
            if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Customer") {
                frappe.set_route("List", "Customer");
            }
            
            // Method 3: Refresh customer link fields
            if (cur_frm && cur_frm.fields_dict) {
                Object.keys(cur_frm.fields_dict).forEach(fieldname => {
                    const field = cur_frm.fields_dict[fieldname];
                    if (field && field.df && field.df.options === "Customer") {
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
                label: __("Kundenname und Typ"),
            },
            {
                label: __("Kundenname"),
                fieldname: "customer_name",
                fieldtype: "Data",
            },
            {
                label: __("Kundentyp"),
                fieldname: "customer_type",
                fieldtype: "Select",
                options: ["Company", "Individual"],
            },
            {
                fieldtype: 'Column Break',
            },
            {
                fieldtype: "Section Break",
                label: __("Contact"),
            },
            {
                label: __("E-Mail-Adresse"),
                fieldname: "email_address",
                fieldtype: "Data",
                options: "Email",
            },
            {
                label: __("Telefon"),
                fieldname: "custom_telefon",
                fieldtype: "Data",
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __("Mobilfunknummer"),
                fieldname: "mobile_number",
                fieldtype: "Data",
            },
            {
                fieldtype: 'Section Break',
                label: __('Steuerdetails'),
            },
            {
                label: __('UmSt.-ID'),
                fieldname: 'tax_id',
                fieldtype: 'Data',
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __('Steuernummer'),
                fieldname: 'custom_steuernummer',
                fieldtype: 'Data',
            },
            {
                fieldtype: "Section Break",
                label: __("Adresse"),
            },
            {
                label: __('Namenszusatz '),
                fieldname: 'custom_namenszusatz',
                fieldtype: 'Data',
            },
            {
                label: __("Straße"),
                fieldname: "address_line1",
                fieldtype: "Data",
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __("Postleitzahl"),
                fieldname: "pincode",
                fieldtype: "Data",
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
