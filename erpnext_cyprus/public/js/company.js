frappe.ui.form.on('Company', {
    refresh: function (frm) {
        // Only show Cyprus-specific features for Cyprus companies
        if (!frm.doc.__islocal && frm.doc.country === "Cyprus") {
            // Add "Set Default Accounts" to Cyprus Features dropdown
            frm.add_custom_button(__('Set Default Accounts'), function () {
                frappe.call({
                    method: "erpnext_cyprus.setup.company.set_cyprus_default_accounts",
                    args: {
                        company_name: frm.doc.name
                    },
                    callback: function (response) {
                        if (!response.exc) {
                            frappe.msgprint(__('Default accounts have been set successfully.'));
                            frm.reload_doc(); // Reload the form to reflect changes
                        }
                    }
                });
            }, __("Cyprus Features"));
            
            // Add "Create Cyprus Tax Templates" to Cyprus Features dropdown
            frm.add_custom_button(__('Create Tax Templates'), function() {
                frappe.call({
                    method: "erpnext_cyprus.setup.install.setup_cyprus_tax_templates",
                    args: {
                        company: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.message && r.message.status === "success") {
                            frappe.msgprint({
                                title: __('Success'),
                                indicator: 'green',
                                message: r.message.message
                            });
                        } else if (r.message && r.message.status === "error") {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: r.message.message
                            });
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: __('Failed to create Cyprus tax templates.')
                            });
                        }
                    }
                });
            }, __("Cyprus Features"));
        }
    },
    
    // Additional functionality for when country is changed to Cyprus
    country: function(frm) {
        if (frm.doc.country === 'Cyprus' && frm.doc.__islocal) {
            frm.set_value('chart_of_accounts', 'Cyprus Standard');
            frm.set_value('default_currency', 'EUR');
            frm.refresh_field('chart_of_accounts');
            
            frappe.show_alert({
                message: __('Cyprus Standard Chart of Accounts selected. Tax templates will be created after company setup.'),
                indicator: 'green'
            });
        }
    }
});