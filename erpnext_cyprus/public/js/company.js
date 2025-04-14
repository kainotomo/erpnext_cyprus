frappe.ui.form.on('Company', {
    refresh: function (frm) {
        // Add a button to trigger default account setup for Cyprus companies
        if (!frm.doc.__islocal && frm.doc.country === "Cyprus") {
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
            }).addClass('btn-primary');
        }
    }
});