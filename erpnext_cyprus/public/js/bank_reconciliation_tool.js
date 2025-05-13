frappe.ui.form.on('Bank Reconciliation Tool', {
    refresh: function (frm) {
        frm.trigger('check_hellenic_bank');
    },
    
    bank_account: function(frm) {
        frm.trigger('check_hellenic_bank');
    },
    
    check_hellenic_bank: function(frm) {
        // Clear any existing Hellenic Bank buttons
        frm.remove_custom_button(__('Retrieve Bank Transactions'), "Hellenic Bank");
        
        if(frm.doc.bank_account) {
            // Get the bank of the selected bank account
            frappe.db.get_value('Bank Account', frm.doc.bank_account, 'bank', function(r) {
                if(r && r.bank) {
                    // Find the specific Hellenic Bank document that serves this bank
                    frappe.db.get_list('Hellenic Bank', {
                        filters: {'bank': r.bank, 'disabled': 0},
                        fields: ['name'],
                        limit: 1
                    }).then(function(hellenic_banks) {
                        if(hellenic_banks && hellenic_banks.length > 0) {
                            const hellenic_bank_name = hellenic_banks[0].name;
                            
                            // Show the Retrieve Bank Transactions button
                            frm.add_custom_button(__('Retrieve Bank Transactions'), function() {
                                if(frm.doc.bank_statement_from_date && frm.doc.bank_statement_to_date) {
                                    // Get the actual document first
                                    frappe.model.with_doc('Hellenic Bank', hellenic_bank_name, function() {
                                        var hellenic_bank_doc = frappe.model.get_doc('Hellenic Bank', hellenic_bank_name);
                                        
                                        // Now call the method directly on the document
                                        frappe.call({
                                            method: "get_bank_transactions",
                                            doc: hellenic_bank_doc,
                                            args: {
                                                bank_account: frm.doc.bank_account,
                                                bank_statement_from_date: frm.doc.bank_statement_from_date,
                                                bank_statement_to_date: frm.doc.bank_statement_to_date
                                            },
                                            freeze: true,
                                            freeze_message: __('Retrieving transactions from Hellenic Bank...'),
                                            callback: function(response) {
                                                if(response.message && response.message.errors) {
                                                    frappe.msgprint(__("Error retrieving transactions: {0}", 
                                                        [response.message.errors]), __("Error"));
                                                } else {
                                                    frappe.msgprint(__("Successfully retrieved bank transactions"));
                                                    // Refresh the reconciliation tool to show new transactions
                                                    frm.trigger("make_reconciliation_tool");
                                                }
                                            }
                                        });
                                    });
                                } else {
                                    frappe.msgprint(__("Please select From Date and To Date"));
                                }
                            }, __("Hellenic Bank"));
                        }
                    });
                }
            });
        }
    }
});