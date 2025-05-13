// Copyright (c) 2023, KAINOTOMO PH LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hellenic Bank', {
	refresh: function (frm) {

		if (!frm.is_new()) {
			// Update token status display
			update_token_status(frm);

			frm.add_custom_button(__("Connect to {}", [frm.doc.title]), async () => {
				frappe.call({
					method: "initiate_web_application_flow",
					doc: frm.doc,
					callback: function (r) {
						window.open(r.message);
					},
				});
			});

			if (frm.doc.authorization_code) {
				frm.add_custom_button(__('Create Accounts'), function () {
					frappe.confirm('Are you sure you want to proceed?', function() {
						frappe.call({
							method: "create_accounts",
							doc: frm.doc,
							callback: function(response) {
								if (response.message.errors === null) {
									frappe.msgprint("You succesfully created the bank accounts.");
								} else {
									frappe.msgprint("Something went wrong.", 'Error');
								}
							}
						});		
					}, function() {
						// action to perform if No is selected
					});			
				});
			}			
		}

	},
	onload: function(frm) {
		// Update token status display
		update_token_status(frm);

		frm.set_query('parent_account', function(doc) {
			return {
				filters: {
					"is_group": 1,
					"company": doc.company
				}
			};
		});
	}
});

// Function to format and display token status in HTML
function update_token_status(frm) {
	let token_status_html = "";
	
	// If no authorization code exists, show warning
	if (!frm.doc.authorization_code) {
		token_status_html = `
			<div class="alert alert-danger">
				<i class="fa fa-exclamation-triangle"></i>
				<strong>No authorization code available.</strong> Please connect to get a token.
			</div>
		`;
	} else {
		token_status_html = `
			<div class="alert alert-success">
				Authorization code is available!!!<br/>
				If you are dealing with any issues try to connect again.
			</div>
		`;
	}
	
	// Update the token_status field with our formatted HTML
	frm.set_df_property("token_status", "options", token_status_html);
}
