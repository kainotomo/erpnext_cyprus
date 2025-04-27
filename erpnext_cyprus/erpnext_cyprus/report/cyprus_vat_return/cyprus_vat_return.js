frappe.query_reports["Cyprus VAT Return"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            fieldname: "date_range",
            label: __("Date Range"),
            fieldtype: "DateRange",
            reqd: 1
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname == "amount" && data && data.bold) {
            value = "<b>" + value + "</b>";
        }
        return value;
    }
};
