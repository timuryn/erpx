frappe.provide("frappe.ui.form");

frappe.ui.form.CustomerQuickEntryForm = class CustomerQuickEntryForm extends frappe.ui.form.QuickEntryForm {
    constructor(doctype, after_insert) {
        super(doctype, after_insert);
        this.skip_redirect_on_error = true;
    }

    render_dialog() {
        this.mandatory = this.get_field();
        super.render_dialog();
        this.bind_phone_validations();
    }

    // Bind directly to the rendered inputs rather than relying on the field
    // dict's `onchange`, which isn't reliably preserved once the Dialog
    // rebuilds field objects for custom fields.
    bind_phone_validations() {
        const phone_fields = [
            { fieldname: "custom_telefon", label: __("Telefon") },
            { fieldname: "mobile_number", label: __("Mobilfunknummer") },
        ];

        phone_fields.forEach(({ fieldname, label }) => {
            const field = this.dialog.get_field(fieldname);
            if (field && field.$input) {
                field.$input.on("input blur", () => {
                    this.validate_phone_field(fieldname, label);
                });
            }
        });
    }

    insert() {
        // ── BLOCK SAVE IF PHONE FIELDS CONTAIN NON-DIGIT CHARACTERS ──
        const phone_fields = [
            { fieldname: "custom_telefon", label: __("Telefon") },
            { fieldname: "mobile_number", label: __("Mobilfunknummer") },
        ];

        const invalid_fields = phone_fields.filter(({ fieldname }) => {
            const value = this.dialog.get_value(fieldname);
            return value && /[-/]/.test(value);
        });

        if (invalid_fields.length) {
            invalid_fields.forEach(({ fieldname, label }) => this.validate_phone_field(fieldname, label));
            frappe.msgprint({
                title: __("Ungültige Telefonnummer"),
                message: __("Bitte entferne Bindestriche (-) und Schrägstriche (/) aus: {0}", [
                    invalid_fields.map(f => f.label).join(", ")
                ]),
                indicator: "red"
            });
            return Promise.reject();
        }
        // ── END ──

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

        return super.insert().then((response) => {
            // response can be the doc itself or wrapped in .message depending on Frappe version
            const customer = response && response.message ? response.message : response;

            // ── CREATE ADDRESS + UPDATE primary_address ──
            if (customer && customer.name && this.dialog.doc.address_line1) {
                const address_doc = {
                    doctype: "Address",
                    address_title: customer.customer_name || customer.name,
                    address_line1: this.dialog.doc.address_line1,
                    address_line2: this.dialog.doc.custom_namenszusatz || "",
                    pincode: this.dialog.doc.pincode,
                    city: this.dialog.doc.city,
                    country: this.dialog.doc.country || "Germany",
                    is_primary_address: 1,
                    is_primary_billing: 1,
                    links: [{
                        link_doctype: "Customer",
                        link_name: customer.name
                    }]
                };

                frappe.call({
                    method: "frappe.client.insert",
                    args: { doc: address_doc },
                    callback: (r) => {
                        if (r.message) {
                            // Build the same HTML format your existing customers use
                            const street_parts = [
                                this.dialog.doc.address_line1,
                                this.dialog.doc.custom_namenszusatz
                            ].filter(Boolean);
                            const street = street_parts.join(" ");
                            const city_line = [this.dialog.doc.pincode, this.dialog.doc.city]
                                .filter(Boolean).join(" ");
                            const country = (this.dialog.doc.country === "Germany" || !this.dialog.doc.country)
                                ? "Deutschland"
                                : this.dialog.doc.country;

                            const html_lines = [street, city_line, country].filter(Boolean);
                            const html = html_lines.join("<br>\n\n    ") + "\n";

                            // Write it back to Customer so link search shows it immediately
                            frappe.db.set_value("Customer", customer.name, "primary_address", html);
                        }
                    }
                });
            }
            // ── END ──

            // Refresh logic (unchanged)
            if (cur_list && cur_list.doctype === "Customer") {
                cur_list.refresh();
            }
            if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Customer") {
                frappe.set_route("List", "Customer");
            }
            if (cur_frm && cur_frm.fields_dict) {
                Object.keys(cur_frm.fields_dict).forEach(fieldname => {
                    const field = cur_frm.fields_dict[fieldname];
                    if (field && field.df && field.df.options === "Customer") {
                        field.refresh();
                    }
                });
            }
            frappe.ui.form.trigger_refresh_field_group && frappe.ui.form.trigger_refresh_field_group();

            return response;
        });
    }

    // ── PHONE NUMBER SYMBOL CHECK ──
    // Warns (non-blocking) when a phone field contains anything other than digits.
    validate_phone_field(fieldname, label) {
        const field = this.dialog.get_field(fieldname);
        const value = this.dialog.get_value(fieldname);
        const is_valid = !value || !/[-/]/.test(value);

        if (field && field.$wrapper) {
            field.$wrapper.toggleClass("has-error", !is_valid);
        }

        if (!is_valid) {
            frappe.show_alert({
                message: __("{0} sollte keine Bindestriche oder Schrägstriche enthalten", [label]),
                indicator: "orange"
            });
        }
    }
    // ── END ──

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
