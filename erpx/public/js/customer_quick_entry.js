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

    // Ensure correct mapping for email, phone, and mobile
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
                label: __('Steuernummer'),
                fieldname: 'tax_id',
                fieldtype: 'Data',
            },
            {
                fieldtype: 'Column Break',
            },
            {
                label: __('UmSt.-ID'),
                fieldname: 'custom_umstid',
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
