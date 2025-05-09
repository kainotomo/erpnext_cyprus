# Copyright (c) 2023, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import base64
import requests
import json
from datetime import datetime
from urllib.parse import urlencode, urljoin

class HellenicBank(Document):

	scopes = [
		"b2b.account.details",
		"b2b.credit.transfer.mass",
		"b2b.account.list",
		"b2b.report.account.statements",
		"b2b.credit.transfer.cancel",
		"b2b.report.credit.transfer.single",
		"b2b.credit.transfer.single",
		"b2b.funds.availability",
		"b2b.report.credit.transfer.mass"
		]

	def validate(self):
		base_url = frappe.utils.get_url()
		callback_path = (
			"/api/method/erpnext_cyprus.erpnext_cyprus.doctype.hellenic_bank.hellenic_bank.callback/" + self.name
		)
		self.redirect_uri = urljoin(base_url, callback_path)

		# run if client_secrent is changed
		string_to_encode = self.client_id + ':' + self.get_password("client_secret")
		self.encoded_auth = base64.b64encode(string_to_encode.encode("utf-8")).decode("utf-8")

	def base64_encode(self, string):
		string_bytes = string.encode('utf-8')  # Convert string to bytes using UTF-8 encoding
		encoded_bytes = base64.b64encode(string_bytes)  # Base64 encode the bytes
		encoded_string = encoded_bytes.decode('utf-8')  # Convert the encoded bytes back to a string
		return encoded_string

	def get_base_url_auth(self):
		return "https://sandbox-oauth.hellenicbank.com" if self.is_sandbox else "https://oauthprod.hellenicbank.com"

	def get_base_url_api(self):
		return "https://sandbox-apis.hellenicbank.com" if self.is_sandbox else "https://apisprod.hellenicbank.com"

	@frappe.whitelist()
	def initiate_web_application_flow(self, user=None, success_uri=None):
		"""Return an authorization URL for the user. Save state in Token Cache."""
		user = user or frappe.session.user		
		authorization_url = self.get_base_url_auth() + "/oauth2/auth"
		state = self.base64_encode(frappe.generate_hash(length=10))
		frappe.db.set_value('Hellenic Bank', self.name, 'state', state)
		query_params = {
			"response_type": "code",
			"client_id": self.client_id,
			"redirect_uri": self.redirect_uri,
			"scope": " ".join(self.scopes),
			"state": state
		}
		authorization_url += "?" + urlencode(query_params)
		return authorization_url
	
	def refresh_token(self):
		authorization_code = json.loads(self.authorization_code)

		# Check if the token is expired
		now = datetime.now()
		expires_at = datetime.fromtimestamp(authorization_code["expires_at"] / 1000)
		if now > expires_at:
			url = self.get_base_url_auth() + "/token"
			payload = {
				"grant_type": "refresh_token",
				"refresh_token": authorization_code["refresh_token"]
			}
			string_to_encode = self.client_id + ':' + self.get_password("client_secret")
			headers = {
				"Authorization": "Basic " + base64.b64encode(string_to_encode.encode("utf-8")).decode("utf-8")
			}

			response = requests.post(url, data=payload, headers=headers)
			response_json = response.json()
			if (response.status_code != 200):
				frappe.throw(response_json["error"] + " - Authorize and try again")
			frappe.db.set_value('Hellenic Bank', self.name, 'authorization_code', response.text)
			frappe.db.commit()
			return response.json()
		else:
			return authorization_code
		
	@frappe.whitelist()
	def create_accounts(self):
		authorization_code = self.refresh_token()
		url = self.get_base_url_api() + "/v1/b2b/account/list"
		payload = {}
		headers = {
			"Authorization": "Bearer " + authorization_code["access_token"],
			"x-client-id": self.client_id	
		}

		response = requests.get(url, params=payload, headers=headers)
		response_json = response.json()
		if (response.status_code != 200):
			return response_json
		
		accounts = response_json["payload"]["accounts"]
		for account in accounts:
			if not frappe.db.exists('Bank Account', account["accountName"] + " - " + self.bank):
				new_account = frappe.get_doc({
					'doctype': 'Account',
					'account_name': account["accountName"],
					'parent_account': self.parent_account,
					'account_type': 'Bank',
					'account_currency': account["accountCurrencyCodes"],
				})
				new_account.insert()

				bank_account = frappe.get_doc({
					'doctype': 'Bank Account',
					'account_name': account["accountName"],
					'account': new_account.name,
					'is_company_account': True,
					'bank': self.bank,
					'bank_account_no': account["accountNumber"],
					'currency': account["accountCurrencyCodes"],
					'iban': account["iban"],
				})
				bank_account.insert()
				
		return response_json

	@frappe.whitelist()
	def get_bank_transactions(self, bank_account, bank_statement_from_date, bank_statement_to_date):

		bank_account_doc = frappe.get_doc("Bank Account", bank_account)
		dateFrom = datetime.strptime(bank_statement_from_date, '%Y-%m-%d').strftime('%Y%m%d0000')
		dateTo = datetime.strptime(bank_statement_to_date, '%Y-%m-%d').strftime('%Y%m%d2359')

		authorization_code = self.refresh_token()
		url = self.get_base_url_api() + "/v1/b2b/account/report"
		payload = {
			"dateTo": dateTo,
			"dateFrom": dateFrom,
			"account": bank_account_doc.iban
		}
		headers = {
			"Authorization": "Bearer " + authorization_code["access_token"],
			"x-client-id": self.client_id	
		}

		response = requests.get(url, params=payload, headers=headers)
		response_json = response.json()
		if (response.status_code != 200):
			return response_json
		
		transactions = response_json["payload"]["transactions"]
		for transaction in transactions:
			filters = {
				'date': transaction["transactionValueDate"],
				'reference_number': transaction["customerReference"]
			}
			amount = transaction["transactionAmount"]
			if amount > 0:
				filters["deposit"] = abs(amount)
			else:
				filters["withdrawal"] = abs(amount)
			existing = frappe.db.get_list('Bank Transaction', filters=filters)

			if (len(existing) == 0):
				bank_transaction = frappe.get_doc({
					"doctype": "Bank Transaction",
					"bank_account": bank_account,
					"status": "Pending",
					"date": transaction["transactionValueDate"],
					"reference_number": transaction["customerReference"],
					"description": transaction["paymentNotes"],
				})
				if amount > 0:
					bank_transaction.deposit = abs(amount)
				else:
					bank_transaction.withdrawal = abs(amount)

				bank_transaction.insert()
				bank_transaction.submit()
				
		return response_json
	
	@frappe.whitelist()
	def single_payment(self, bank_account, party_bank_account, paid_amount, reference_no, reference_date, party_name):

		debtorBank = frappe.db.get_value('Bank Account', bank_account, 'bank')
		debtorBic = frappe.db.get_value('Bank', debtorBank, 'swift_number')
		debtorAccount = frappe.db.get_value('Bank Account', bank_account, 'iban')

		beneficiaryBank = frappe.db.get_value('Bank Account', party_bank_account, 'bank')
		beneficiaryBankBic = frappe.db.get_value('Bank', beneficiaryBank, 'swift_number')
		beneficiaryAccount = frappe.db.get_value('Bank Account', party_bank_account, 'iban') 

		self.refresh_token()
		authorization_code = json.loads(self.authorization_code)
		url = self.get_base_url_api() + "/v1/b2b/credit/transfer"
		payload = {
			"executionDate": reference_date,
			"amount": paid_amount,
			"debtorAccount": debtorAccount,
			"beneficiaryAccount": beneficiaryAccount,
			"beneficiaryName": party_name,
			"currency": "EUR",
			"debtorBic": debtorBic,
			"beneficiaryBankBic": beneficiaryBankBic,
			"customerReference": reference_no,
			"paymentNotes": reference_no
		}
		headers = {
			"Authorization": "Bearer " + authorization_code["access_token"],
			"x-client-id": self.client_id,
			'Content-Type': 'application/json'
		}

		response = requests.post(url, json=payload, headers=headers)
		response_json = response.json()
		if (response.status_code != 200):
			error_message = "Error processing payment"
			
			try:
				if "errors" in response_json and response_json["errors"]:
					errors = []
					for error in response_json["errors"]:
						if "message" in error and error["message"]:
							errors.append(error["message"])
						elif "code" in error:
							errors.append(f"Error code: {error['code']}")
						
						# Handle the nested params structure
						if "params" in error and error["params"]:
							for param_group in error["params"]:
								for param in param_group:
									if "errorCode" in param and "field" in param and "exposedName" in param["field"]:
										field_name = param["field"]["exposedName"]
										error_code = param["errorCode"]
										errors.append(f"Field '{field_name}': {error_code}")
					
					if errors:
						error_message = "Payment errors:\n• " + "\n• ".join(errors)
				elif "payload" in response_json and "message" in response_json["payload"]:
					error_message = response_json["payload"]["message"]
			except Exception as e:
				frappe.log_error(f"Error parsing Hellenic Bank response: {str(e)}\nResponse: {response_json}", 
								 "Hellenic Bank API Error")
			
			frappe.throw(error_message)
		
		return response_json

@frappe.whitelist(methods=["GET"], allow_guest=True)
def callback(code=None, state=None):
	"""Handle client's code.

	Called during the oauthorization flow by the remote oAuth2 server to
	transmit a code that can be used by the local server to obtain an access
	token.
	"""

	if frappe.session.user == "Guest":
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/login?" + urlencode({"redirect-to": frappe.request.url})
		return

	path = frappe.request.path[1:].split("/")
	if len(path) != 4 or not path[3]:
		frappe.throw(_("Invalid Parameters."))

	hellenic_bank = frappe.get_doc("Hellenic Bank", path[3])

	if state != hellenic_bank.state:
		frappe.throw(_("Invalid token state! Check if the token has been created by the OAuth user."))

	url = hellenic_bank.get_base_url_auth() + "/token/exchange"
	payload = {
		"grant_type": "authorization_code",
		"redirect_uri": hellenic_bank.redirect_uri,
		"code": code
	}
	headers = {
		"Authorization": "Basic " + hellenic_bank.encoded_auth
	}

	response = requests.post(url, data=payload, headers=headers)
	if (response.status_code != 200):
		frappe.throw(response.text)
	frappe.db.set_value('Hellenic Bank', hellenic_bank.name, 'authorization_code', response.text)
	frappe.db.set_value('Hellenic Bank', hellenic_bank.name, 'code', code)
	frappe.db.commit()

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = hellenic_bank.get_url()
