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

			frm.add_custom_button(__('Create Accounts'), function () {
				frappe.confirm('Are you sure you want to proceed?', function() {
					frappe.call({
						method: "erpnext_cyprus.erpnext_cyprus.doctype.hellenic_bank.hellenic_bank.create_accounts",
						args: {
							// your arguments here
						},
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

		frm.add_custom_button(__('Authorize'), function () {
			let urlParams = new URLSearchParams(window.location.search);
			if (urlParams.get('state') === null) {
				let is_sandbox = frm.get_field('is_sandbox').value;
				let base_url = is_sandbox ? "https://sandbox-oauth.hellenicbank.com" : "https://oauthprod.hellenicbank.com";
				let client_id = frm.get_field('client_id').value;
				let href = base_url + "/oauth2/auth?response_type=code&client_id=" + client_id +
					"&redirect_uri=" + window.location.href +
					"&scope=b2b.account.details,b2b.credit.transfer.mass,b2b.account.list,b2b.report.account.statements,b2b.credit.transfer.cancel,b2b.report.credit.transfer.single,b2b.credit.transfer.single,b2b.funds.availability,b2b.report.credit.transfer.mass" +
					"&state=erpnext_state_b64_encoded";
				window.location.href = href;
				frappe.validated = true;
			}
		});

		let urlParams = new URLSearchParams(window.location.search);
		let new_code = urlParams.get('code');
		if (new_code !== null) {
			frappe.db.get_single_value('Hellenic Bank', 'code')
				.then(function (old_code) {
					if ((urlParams.get('state') === "erpnext_state_b64_encoded") && (new_code !== old_code)) {
						frappe.db.set_value('Hellenic Bank', frm.doc.name, 'code', new_code)
							.then(r => {
								let doc = r.message;
								frappe.call({
									method: "cyprus_banks.cyprus_banks.doctype.hellenic_bank.hellenic_bank.get_authorization_code",
									args: {
										// your arguments here
									},
									callback: function(response) {
										if ('error' in response.message) {
											frappe.msgprint(response.message.error);
										} else {
											frappe.msgprint("You succesfully received a new authorization code.");
										}
									}
								});								
							})
					}
				});
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
			<div class="alert alert-warning">
				<i class="fa fa-exclamation-triangle"></i>
				<strong>No token available.</strong> Please authorize to get a token.
			</div>
		`;
	} else {
		try {
			// Parse token data from JSON
			const token_data = JSON.parse(frm.doc.authorization_code);
			
			// Extract token information
			const created_on_timestamp = token_data.created_on ? token_data.created_on : 0;
			const expires_at_timestamp = token_data.expires_at ? token_data.expires_at : 0;
			
			const created_on = new Date(created_on_timestamp);
			const expires_at = new Date(expires_at_timestamp);
			const now = new Date();
			const is_valid = now < expires_at;
			
			// Calculate time remaining
			let time_remaining_text = "Expired";
			if (is_valid) {
				const time_remaining_ms = expires_at - now;
				const minutes_remaining = Math.floor(time_remaining_ms / (1000 * 60));
				time_remaining_text = `${minutes_remaining} minutes`;
			}
			
			// Format dates for display
			const created_on_str = created_on.toLocaleString();
			const expires_at_str = expires_at.toLocaleString();
			
			// Generate status HTML
			const status_class = is_valid ? "success" : "danger";
			const status_icon = is_valid ? "check-circle" : "times-circle";
			const status_text = is_valid ? "Valid" : "Expired";
			
			token_status_html = `
				<div class="alert alert-${status_class}">
					<i class="fa fa-${status_icon}"></i>
					<strong>Token Status: ${status_text}</strong>
				</div>
				<div class="row">
					<div class="col-md-6">
						<strong>Created On:</strong> ${created_on_str}
					</div>
					<div class="col-md-6">
						<strong>Expires At:</strong> ${expires_at_str}
					</div>
				</div>
				<div class="row mt-2">
					<div class="col-md-12">
						<strong>Time Remaining:</strong> ${time_remaining_text}
					</div>
				</div>
				<div class="row mt-2">
					<div class="col-md-12">
						<strong>Scopes:</strong> ${token_data.scope ? token_data.scope.join(", ") : ""}
					</div>
				</div>
			`;
		} catch (e) {
			// Handle any errors in parsing or processing
			token_status_html = `
				<div class="alert alert-danger">
					<i class="fa fa-exclamation-circle"></i>
					<strong>Error parsing token data:</strong> ${e.message}
				</div>
			`;
		}
	}
	
	// Update the token_status field with our formatted HTML
	frm.set_df_property("token_status", "options", token_status_html);
}
