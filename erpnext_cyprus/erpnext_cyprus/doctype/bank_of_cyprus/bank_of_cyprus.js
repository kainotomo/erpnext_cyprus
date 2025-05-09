// Copyright (c) 2023, KAINOTOMO PH LTD and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bank Of Cyprus', {
	refresh: function (frm) {

		frm.add_custom_button(__('Authorize'), function () {
			frappe.call({
				method: "cyprus_banks.cyprus_banks.doctype.bank_of_cyprus.bank_of_cyprus.get_access_token_1",
				args: {
					// your arguments here
				},
				callback: function (response) {
					if (response.message.errors) {
						frappe.msgprint("Something went wrong.", 'Error');
					} else {
						let urlParams = new URLSearchParams(window.location.search);
						if (urlParams.get('state') === null) {
							let is_sandbox = frm.get_field('is_sandbox').value;
							let base_url = is_sandbox ? "https://sandbox-apis.bankofcyprus.com/df-boc-org-sb/sb/psd2/oauth2/authorize" : "https://apis.bankofcyprus.com/df-boc-org-prd/prod/psd2/oauth2/authorize";
							let client_id = frm.get_field('client_id').value;
							let href = base_url + "?response_type=code" +
								"&redirect_uri=" + window.location.href +
								"&scope=UserOAuth2Security" +
								"&client_id=" + client_id +
								"&subscriptionid=" + response.message.subscriptionId;
							window.location.href = href;
							frappe.validated = true;
						}
					}
				}
			});
		});

		frm.add_custom_button(__('Create Accounts'), function () {
			frappe.confirm('Are you sure you want to proceed?', function () {
				frappe.call({
					method: "cyprus_banks.cyprus_banks.doctype.bank_of_cyprus.bank_of_cyprus.create_accounts",
					args: {
						// your arguments here
					},
					callback: function (response) {
						if (response.message.errors) {
							frappe.msgprint("Something went wrong.", 'Error');
						} else {
							frappe.msgprint("You succesfully created the bank accounts.");
						}
					}
				});
			}, function () {
				// action to perform if No is selected
			});
		});

		let urlParams = new URLSearchParams(window.location.search);
		let new_code = urlParams.get('code');
		if (new_code !== null) {
			frappe.db.get_single_value('Bank Of Cyprus', 'code')
				.then(function (old_code) {
					if (new_code !== old_code) {
						frappe.db.set_value('Bank Of Cyprus', frm.doc.name, 'code', new_code)
							.then(r => {
								let doc = r.message;
								frappe.call({
									method: "cyprus_banks.cyprus_banks.doctype.bank_of_cyprus.bank_of_cyprus.get_access_token_2",
									args: {
										// your arguments here
									},
									callback: function(response) {
										if ('error' in response.message) {
											frappe.msgprint(response.message.error);
										} else {
											frappe.msgprint("You succesfully created a new subscription.");
										}
									}
								});								
							})
					}
				});
		}

	},
	onload: function (frm) {
		frm.set_query('parent_account', function (doc) {
			return {
				filters: {
					"is_group": 1,
					"company": doc.company
				}
			};
		});
	}
});
