frappe.ui.form.on('Company', {
    refresh: function (frm) {
        // Only show Cyprus-specific features for Cyprus companies
        if (!frm.doc.__islocal && frm.doc.country === "Cyprus") {
            // Add "Setup Cyprus Company" to Cyprus Features dropdown
            frm.add_custom_button(__('Finish Setup'), function() {
                frappe.call({
                    method: "erpnext_cyprus.setup.company.setup_cyprus_company",
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

            // Add "Create Sample Data" to Cyprus Features dropdown
            frm.add_custom_button(__('Create Sample Data'), function () {
                frappe.confirm(
                    __('Are you sure you want to create sample data for this company?'),
                    function () {
                        frappe.call({
                            method: "erpnext_cyprus.setup.sample_data.create_sample_data",
                            args: {
                                company: frm.doc.name
                            },
                            callback: function (response) {
                                if (response.message && response.message.status === "success") {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: response.message.message
                                    });
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: __('Error'),
                                        indicator: 'red',
                                        message: response.message ? response.message.message : __('Failed to create sample data.')
                                    });
                                }
                            }
                        });
                    }
                );
            }, __("Cyprus Features"));

            // Add "Delete Sample Data" to Cyprus Features dropdown
            frm.add_custom_button(__('Delete Sample Data'), function () {
                frappe.confirm(
                    __('Are you sure you want to delete all sample data for this company?'),
                    function () {
                        frappe.call({
                            method: "erpnext_cyprus.setup.sample_data.delete_sample_data",
                            args: {
                                company: frm.doc.name
                            },
                            callback: function (response) {
                                if (response.message && response.message.status === "success") {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: response.message.message
                                    });
                                    frm.reload_doc();
                                } else {
                                    frappe.msgprint({
                                        title: __('Error'),
                                        indicator: 'red',
                                        message: response.message ? response.message.message : __('Failed to delete sample data.')
                                    });
                                }
                            }
                        });
                    }
                );
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