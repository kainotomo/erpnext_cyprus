frappe.ui.form.on('Payment Entry', {
    refresh: function (frm) {
        frm.trigger('check_hellenic_bank_transfer');
    },
    
    bank_account: function(frm) {
        frm.trigger('check_hellenic_bank_transfer');
    },
    
    party_bank_account: function(frm) {
        frm.trigger('check_hellenic_bank_transfer');
    },
    
    check_hellenic_bank_transfer: function(frm) {
        // Clear any existing Hellenic Bank buttons
        frm.remove_custom_button(__('Wire Transfer'), "Hellenic Bank");
        
        if(frm.doc.bank_account && frm.doc.party_bank_account) {
            // Get the bank of the selected bank account
            frappe.db.get_value('Bank Account', frm.doc.bank_account, 'bank', function(r) {
                if(r && r.bank) {
                    // Check if this bank is linked to any Hellenic Bank doctype
                    frappe.db.get_list('Hellenic Bank', {
                        filters: {'bank': r.bank},
                        fields: ['name'],
                        limit: 1
                    }).then(function(hellenic_banks) {
                        if(hellenic_banks && hellenic_banks.length > 0) {
                            const hellenic_bank_name = hellenic_banks[0].name;
                            
                            // Add the Wire Transfer button
                            frm.add_custom_button(__('Wire Transfer'), function() {
                                if(frm.doc.payment_type == "Pay" && 
                                   frm.doc.paid_amount && 
                                   frm.doc.reference_no && 
                                   frm.doc.reference_date && 
                                   frm.doc.party_name) {
                                    
                                    // Get the Hellenic Bank doc and call the method
                                    frappe.model.with_doc('Hellenic Bank', hellenic_bank_name, function() {
                                        var hellenic_bank_doc = frappe.model.get_doc('Hellenic Bank', hellenic_bank_name);
                                        
                                        frappe.call({
                                            method: "single_payment",
                                            doc: hellenic_bank_doc,
                                            args: {
                                                bank_account: frm.doc.bank_account,
                                                party_bank_account: frm.doc.party_bank_account,
                                                paid_amount: frm.doc.paid_amount,
                                                reference_no: frm.doc.reference_no,
                                                reference_date: frm.doc.reference_date,
                                                party_name: frm.doc.party_name
                                            },
                                            freeze: true,
                                            freeze_message: __('Processing payment via Hellenic Bank...'),
                                            callback: function(response) {
                                                if(response.message && !response.message.errors) {
                                                    frappe.msgprint(__("Payment successfully processed through Hellenic Bank"));
                                                    frm.reload_doc();
                                                }
                                            }
                                        });
                                    });
                                } else {
                                    frappe.msgprint(__("Payment type must be Pay, and all of these fields are required: Paid Amount, Reference No, Reference Date, and Party Name"));
                                }
                            }, __("Hellenic Bank"));
                        }
                    });
                }
            });
        }
    }
});