frappe.ui.form.on('Company', {
    refresh: function(frm) {
        // Only show button if company exists (has been saved) and country is Cyprus
        if (frm.doc.name && !frm.is_new() && frm.doc.country === 'Cyprus') {
            frm.add_custom_button(__('Setup Cyprus Company'), function() {
                frappe.confirm(
                    __('This will set up the Cyprus company with:<br>1. Extended chart of accounts<br>2. Tax categories<br><br>Proceed?'),
                    function() {
                        frappe.call({
                            method: 'erpnext_cyprus.api.setup_cyprus_company',
                            args: {
                                company: frm.doc.name
                            },
                            freeze: true,
                            freeze_message: __('Setting up Cyprus Company...'),
                            callback: function(r) {
                                if (!r.exc) {
                                    let message = __('Cyprus Company has been set up successfully.');
                                    
                                    // Add details about what was created
                                    if (r.message.accounts_added && r.message.accounts_added.length > 0) {
                                        message += '<br><br><b>' + __('Accounts created:') + '</b><br>';
                                        message += r.message.accounts_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new accounts needed to be created.');
                                    }
                                    
                                    if (r.message.tax_categories_added && r.message.tax_categories_added.length > 0) {
                                        message += '<br><br><b>' + __('Tax categories created:') + '</b><br>';
                                        message += r.message.tax_categories_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new tax categories needed to be created.');
                                    }
                                    
                                    frappe.msgprint({
                                        title: __('Success'),
                                        indicator: 'green',
                                        message: message
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