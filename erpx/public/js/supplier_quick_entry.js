frappe.provide("frappe.ui.form");

frappe.ui.form.SupplierQuickEntryForm = class SupplierQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
        console.log("SupplierQuickEntryForm constructor called");
    }
    
    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
        console.log("SupplierQuickEntryForm dialog rendered");
    }
    
    // Handle field mapping for supplier-specific fields
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
        
        return super.insert();
    }
    
    // Define the fields in the quick entry form
    get_field() {
        console.log("SupplierQuickEntryForm get_field called");
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
                label: __("Lieferantendetails"),
                fieldname: "supplier_details",
                fieldtype: "Text",
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __("E-Mail-Adresse"),
                fieldname: "email_address",
                fieldtype: "Data",
                options: "Email",
            },
            {
                label: __("Webseite"),
                fieldname: "website",
                fieldtype: "Data",
            },
            {
                label: __("Mobilfunknummer"),
                fieldname: "mobile_number",
                fieldtype: "Data",
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

