frappe.query_reports["Cyprus VAT Return"] = {
    "filters": [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        {
            fieldname: "date_range",
            label: __("Date Range"),
            fieldtype: "DateRange",
            reqd: 1
        },
        {
            fieldname: "output_vat_account",
            label: __("Output VAT Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function() {
                return {
                    filters: {
                        'account_type': 'Tax',
                        'company': frappe.query_report.get_filter_value("company")
                    }
                };
            },
            reqd: 1
        },
        {
            fieldname: "input_vat_account",
            label: __("Input VAT Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function() {
                return {
                    filters: {
                        'account_type': 'Tax',
                        'company': frappe.query_report.get_filter_value("company")
                    }
                };
            },
            reqd: 1
        }
    ],
    
    onload: function(report) {
        report.page.add_inner_button(__("Set Default Accounts"), function() {
            set_default_vat_accounts(report);
        });
        
        // Set default accounts when report first loads
        report.page.add_inner_message(__("Loading default VAT accounts..."));
        setTimeout(function() {
            set_default_vat_accounts(report);
            report.page.clear_inner_message();
        }, 1000); // Give the report a second to fully initialize
    }
};

// Function to set the default VAT accounts based on account numbers
function set_default_vat_accounts(report) {
    const company = report.get_filter_value('company');
    if (!company) return;
    
    // Set default Output VAT account (2312)
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Account",
            filters: {
                "company": company,
                "account_number": "2312",
                "account_type": "Tax"
            },
            fields: ["name"],
            limit_page_length: 1
        },
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                report.set_filter_value('output_vat_account', response.message[0].name);
            } else {
                // Try with a broader search if exact match isn't found
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Account",
                        filters: {
                            "company": company,
                            "account_type": "Tax",
                            "name": ["like", "%Output VAT%"]
                        },
                        fields: ["name"],
                        limit_page_length: 1
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            report.set_filter_value('output_vat_account', r.message[0].name);
                        }
                    }
                });
            }
        }
    });
    
    // Set default Input VAT account (1520)
    frappe.call({
        method: "frappe.client.get_list",
        args: {
            doctype: "Account",
            filters: {
                "company": company,
                "account_number": "1520",
                "account_type": "Tax"
            },
            fields: ["name"],
            limit_page_length: 1
        },
        callback: function(response) {
            if (response.message && response.message.length > 0) {
                report.set_filter_value('input_vat_account', response.message[0].name);
            } else {
                // Try with a broader search if exact match isn't found
                frappe.call({
                    method: "frappe.client.get_list",
                    args: {
                        doctype: "Account",
                        filters: {
                            "company": company,
                            "account_type": "Tax",
                            "name": ["like", "%Input VAT%"]
                        },
                        fields: ["name"],
                        limit_page_length: 1
                    },
                    callback: function(r) {
                        if (r.message && r.message.length > 0) {
                            report.set_filter_value('input_vat_account', r.message[0].name);
                        }
                    }
                });
            }
        }
    });
}
