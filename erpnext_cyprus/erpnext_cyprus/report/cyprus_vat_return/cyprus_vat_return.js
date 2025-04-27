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
            "fieldname": "fiscal_year",
            "label": __("Fiscal Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "reqd": 1,
            "on_change": function() {
                updateDateRange();
            }
        },
        {
            "fieldname": "quarter",
            "label": __("Quarter"),
            "fieldtype": "Select",
            "options": [
                "Q1 (Jan-Mar)",
                "Q2 (Apr-Jun)",
                "Q3 (Jul-Sep)",
                "Q4 (Oct-Dec)"
            ],
            "default": getCurrentQuarter(),
            "reqd": 1,
            "on_change": function() {
                updateDateRange();
            }
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "hidden": 1
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "hidden": 1
        }
    ],
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname == "amount" && data && data.bold) {
            value = "<b>" + value + "</b>";
        }
        return value;
    },
    "onload": function(report) {
        // Find and set the current fiscal year
        setCurrentFiscalYear();
        
        report.page.add_inner_button(__("Download Cyprus VAT Format"), function() {
            // This would generate the official VAT format download
            let filters = report.get_values();
            
            frappe.call({
                method: "erpnext_cyprus.erpnext_cyprus.report.cyprus_vat_return.cyprus_vat_return.export_vat_return",
                args: {
                    filters: filters
                },
                callback: function(r) {
                    if (r.message) {
                        window.open(r.message);
                    }
                }
            });
        });
    }
};

function getCurrentQuarter() {
    const currentMonth = new Date().getMonth() + 1; // JavaScript months are 0-indexed
    
    if (currentMonth >= 1 && currentMonth <= 3) return "Q1 (Jan-Mar)";
    if (currentMonth >= 4 && currentMonth <= 6) return "Q2 (Apr-Jun)";
    if (currentMonth >= 7 && currentMonth <= 9) return "Q3 (Jul-Sep)";
    return "Q4 (Oct-Dec)";
}

function setCurrentFiscalYear() {
    const today = frappe.datetime.get_today();
    
    // Find the fiscal year containing today's date
    frappe.db.get_list('Fiscal Year', {
        fields: ['name'],
        filters: {
            'disabled': 0
        }
    }).then(years => {
        const promises = years.map(year => {
            return new Promise(resolve => {
                frappe.db.get_value('Fiscal Year', year.name, ['year_start_date', 'year_end_date'])
                    .then(value => {
                        resolve({
                            name: year.name,
                            start: value.message.year_start_date,
                            end: value.message.year_end_date
                        });
                    });
            });
        });
        
        Promise.all(promises).then(fiscalYears => {
            const currentFY = fiscalYears.find(fy => {
                return today >= fy.start && today <= fy.end;
            });
            
            if (currentFY) {
                frappe.query_report.set_filter_value('fiscal_year', currentFY.name);
                updateDateRange();
            }
        });
    });
}

function updateDateRange() {
    let quarter = frappe.query_report.get_filter_value('quarter');
    let fiscal_year = frappe.query_report.get_filter_value('fiscal_year');
    
    if (!quarter || !fiscal_year) return;
    
    // Get the year part from fiscal year
    frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"], function(value) {
        let year;
        
        // Try to get year from fiscal year value or fallback to extracting from fiscal year name
        if (!value || !value.message || !value.message.year_start_date) {
            
            // Try to extract the year from fiscal year name (which often includes the year)
            const yearMatch = fiscal_year.match(/\d{4}/);
            if (yearMatch) {
                year = yearMatch[0];
            } else {
                // If we can't extract year from name, use current year
                year = new Date().getFullYear();
            }
        } else {
            year = new Date(value.message.year_start_date).getFullYear();
        }
        
        let from_date, to_date;
        
        // Extract quarter value from the display string
        let q = quarter.substring(0, 2);
        
        switch(q) {
            case "Q1":
                from_date = year + "-01-01";
                to_date = year + "-03-31";
                break;
            case "Q2":
                from_date = year + "-04-01";
                to_date = year + "-06-30";
                break;
            case "Q3":
                from_date = year + "-07-01";
                to_date = year + "-09-30";
                break;
            case "Q4":
                from_date = year + "-10-01";
                to_date = year + "-12-31";
                break;
        }
        
        frappe.query_report.set_filter_value('from_date', from_date);
        frappe.query_report.set_filter_value('to_date', to_date);
        frappe.query_report.refresh();
    });
}