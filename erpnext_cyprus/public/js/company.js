frappe.ui.form.on('Company', {
    refresh: function(frm) {
        // Only show button if company exists (has been saved) and country is Cyprus
        if (frm.doc.name && !frm.is_new() && frm.doc.country === 'Cyprus') {
            frm.add_custom_button(__('Setup Cyprus Company'), function() {
                frappe.confirm(
                    __('This will set up the Cyprus company with:<br>1. Extended chart of accounts<br>2. Item groups<br>3. Purchase tax templates<br>4. Sales tax templates<br>5. Item tax templates<br>6. Tax rules<br><br>Proceed?'),
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
                                    
                                    // Item groups info (moved up to match confirmation order)
                                    if (r.message.item_groups_added && r.message.item_groups_added.length > 0) {
                                        message += '<br><br><b>' + __('Item groups created:') + '</b><br>';
                                        message += r.message.item_groups_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new item groups needed to be created.');
                                    }
                                    
                                    if (r.message.purchase_templates_added && r.message.purchase_templates_added.length > 0) {
                                        message += '<br><br><b>' + __('Purchase tax templates created:') + '</b><br>';
                                        message += r.message.purchase_templates_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new purchase tax templates needed to be created.');
                                    }
                                    
                                    // Add sales tax templates info
                                    if (r.message.sales_templates_added && r.message.sales_templates_added.length > 0) {
                                        message += '<br><br><b>' + __('Sales tax templates created:') + '</b><br>';
                                        message += r.message.sales_templates_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new sales tax templates needed to be created.');
                                    }
                                    
                                    // Add item tax templates info
                                    if (r.message.item_tax_templates_added && r.message.item_tax_templates_added.length > 0) {
                                        message += '<br><br><b>' + __('Item tax templates created:') + '</b><br>';
                                        message += r.message.item_tax_templates_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new item tax templates needed to be created.');
                                    }
                                    
                                    // Add tax rules info
                                    if (r.message.tax_rules_added && r.message.tax_rules_added.length > 0) {
                                        message += '<br><br><b>' + __('Tax rules created:') + '</b><br>';
                                        message += r.message.tax_rules_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new tax rules needed to be created.');
                                    }

                                    // Add territories info
                                    if (r.message.territories_added && r.message.territories_added.length > 0) {
                                        message += '<br><br><b>' + __('Territories created:') + '</b><br>';
                                        message += r.message.territories_added.join('<br>');
                                    } else {
                                        message += '<br><br>' + __('No new territories needed to be created.');
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
            }, __('Manage'));
        }
    },
    
    // Also add check when country field changes
    country: function(frm) {
        frm.trigger('refresh');
    }
});