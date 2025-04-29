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
            fieldname: "vat_account",
            label: __("VAT Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: function() {
                return {
                    filters: {
                        'account_type': 'Tax',
                        'is_group': ['in', [0, 1]],
                        'company': frappe.query_report.get_filter_value("company")
                    }
                };
            },
            reqd: 1
        }
    ]
};
