// Copyright (c) 2023, KAINOTOMO PH LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Hellenic Bank', {
	refresh: function (frm) {

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

		frm.add_custom_button(__('Create Accounts'), function () {
			frappe.confirm('Are you sure you want to proceed?', function() {
				frappe.call({
					method: "cyprus_banks.cyprus_banks.doctype.hellenic_bank.hellenic_bank.create_accounts",
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
