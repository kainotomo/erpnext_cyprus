frappe.ui.form.on('Company', {
    refresh: function(frm) {
        // Only show button if company exists (has been saved) and country is Cyprus
        if (frm.doc.name && !frm.is_new() && frm.doc.country === 'Cyprus') {
            frm.add_custom_button(__('Setup Cyprus Chart of Accounts'), function() {
                frappe.confirm(
                    __('This will extend the chart of accounts with Cyprus-specific accounts for handling local, EU, and international transactions. Proceed?'),
                    function() {
                        frappe.call({
                            method: 'erpnext_cyprus.api.setup_cyprus_chart_of_accounts',
                            args: {
                                company: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __('Setting up Cyprus Chart of Accounts...'),
                            callback: function(r) {
                                if (!r.exc) {
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: __('Cyprus Chart of Accounts has been set up successfully.')
                                    });
                                    frm.refresh();
                                }
                            }
                        });
                    }
                );
            }, __('Utilities'));
        }
    },
    
    // Also add check when country field changes
    country: function(frm) {
        frm.trigger('refresh');
    }
});