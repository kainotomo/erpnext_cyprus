# Copyright (c) 2023, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
import json
from datetime import datetime
import uuid
from urllib.parse import urlencode, urljoin
import base64

class BankOfCyprus(Document):
	
	def validate(self):
		base_url = frappe.utils.get_url()
		callback_path = (
			"/api/method/erpnext_cyprus.erpnext_cyprus.doctype.bank_of_cyprus.bank_of_cyprus.callback/" + self.name
		)
		self.redirect_uri = urljoin(base_url, callback_path)

	def get_base_url(self):
		return "https://sandbox-apis.bankofcyprus.com/df-boc-org-sb/sb/psd2" if self.is_sandbox else "https://apis.bankofcyprus.com/df-boc-org-prd/prod/psd2"

	def base64_encode(self, string):
		string_bytes = string.encode('utf-8')  # Convert string to bytes using UTF-8 encoding
		encoded_bytes = base64.b64encode(string_bytes)  # Base64 encode the bytes
		encoded_string = encoded_bytes.decode('utf-8')  # Convert the encoded bytes back to a string
		return encoded_string

	def get_access_token_1(self):

		url = self.get_base_url() + "/oauth2/token"
		payload = {
			"grant_type": "client_credentials",
			"scope": "TPPOAuth2Security",
			"client_id": self.client_id,
			"client_secret": self.get_password("client_secret")
		}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/x-www-form-urlencoded"
		}
		response = requests.post(url, data=payload, headers=headers)
		if (response.status_code != 200):
			return response.json()
		frappe.db.set_value('Bank Of Cyprus', self.name, 'access_token_1', response.text)
		self.access_token_1 = response.text
		
		return self.create_subscription()
	
	def get_access_token_2(self):

		url = self.get_base_url() + "/oauth2/token"
		payload = {
			"grant_type": "authorization_code",
			"scope": "UserOAuth2Security",
			"client_id": self.client_id,
			"client_secret": self.get_password("client_secret"),
			"code": self.code
		}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/x-www-form-urlencoded"
		}
		response = requests.post(url, data=payload, headers=headers)
		if (response.status_code != 200):
			return response.json()
		frappe.db.set_value('Bank Of Cyprus', self.name, 'access_token_2', response.text)
		
		return self.update_subscription()
	
	def create_subscription(self):

		access_token_1 = json.loads(self.access_token_1)
		url = self.get_base_url() + "/v1/subscriptions"
		payload = {
			"accounts": {
				"transactionHistory": True,
				"balance": True,
				"details": True,
				"checkFundsAvailability": True
			},
			"payments": {
				"limit": 99999999,
				"currency": "string",
				"amount":99999999
			},
				"customerInformation": {
				"personalInformation":True,
				"identification":True,
				"address":True,
				"telephone":True,
				"pepinformation":True,
				"reviewInformation":True
			}
		}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"Authorization": "Bearer " + access_token_1["access_token"],
			"timeStamp": datetime.utcnow().isoformat(),
			"journeyId": str(uuid.uuid4())
		}
		response = requests.post(url, json=payload, headers=headers)
		if (response.status_code != 200 and response.status_code != 201):
			frappe.throw("Something went wrong with Bank Of Cyprus authorization")
		frappe.db.set_value('Bank Of Cyprus', self.name, 'subscription_id', response.text)
		return response.json()
	
	def update_subscription(self):

		subscription_id = json.loads(self.subscription_id)
		access_token_2 = json.loads(self.access_token_2)
		url = self.get_base_url() + "/v1/subscriptions/" + subscription_id["subscriptionId"]
		
		# First get the subscription to get accounts
		payload = {}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"Authorization": "Bearer " + access_token_2["access_token"],
			"originUserId": self.user_id,
			"timeStamp": datetime.utcnow().isoformat(),
			"journeyId": str(uuid.uuid4()),
			"app_name": "ERPNext Integration"
		}
		response = requests.get(url, params=payload, headers=headers)
		if (response.status_code != 200 and response.status_code != 201):
			frappe.throw("Something went wrong with Bank Of Cyprus authorization")
		frappe.db.set_value('Bank Of Cyprus', self.name, 'subscription_id', response.text)
		response_json = response.json()[0]

		# Then patch to activate subscription
		payload = {
			"selectedAccounts": response_json["selectedAccounts"],
			"accounts": response_json["accounts"],
			"payments": response_json["payments"],
			"customerInformation": response_json["customerInformation"]
		}
		headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
			"Authorization": "Bearer " + access_token_2["access_token"],
			"originUserId": self.user_id,
			"timeStamp": datetime.utcnow().isoformat(),
			"journeyId": str(uuid.uuid4()),
			"app_name": "ERPNext Integration"
		}
		response = requests.patch(url=url, json=payload, headers=headers)
		if (response.status_code != 200 and response.status_code != 201):
			frappe.throw("Something went wrong with Bank Of Cyprus authorization")
		frappe.db.set_value('Bank Of Cyprus', self.name, 'subscription_id', response.text)
		return response.json()

	@frappe.whitelist()
	def initiate_web_application_flow(self):
		"""Return an authorization URL. Save state in Token Cache."""

		subscription_id = self.get_access_token_1()['subscriptionId']
		
		authorization_url = self.get_base_url() + "/oauth2/authorize"
		state = self.base64_encode(frappe.generate_hash(length=10))
		frappe.db.set_value('Bank Of Cyprus', self.name, 'state', state)
		query_params = {
			"response_type": "code",
			"redirect_uri": self.redirect_uri,
			"scope": "UserOAuth2Security",
			"client_id": self.client_id,
			"subscriptionId": subscription_id,
			"state": state
		}
		authorization_url += "?" + urlencode(query_params)
		return authorization_url

@frappe.whitelist()
def create_accounts():
	bank_of_cyprus = frappe.get_doc("Bank Of Cyprus")
	access_token_1 = json.loads(bank_of_cyprus.access_token_1)
	subscription_id = json.loads(bank_of_cyprus.subscription_id)
	url = get_base_url(bank_of_cyprus) + "/v1/accounts"
	payload = {}
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Bearer " + access_token_1["access_token"],
		"subscriptionId": subscription_id["subscriptionId"],
		"originUserId": bank_of_cyprus.user_id,
		"journeyId": str(uuid.uuid4()),
		"timeStamp": datetime.utcnow().isoformat()
	}

	response = requests.get(url, params=payload, headers=headers)
	if (response.status_code != 200):
		frappe.throw(response.text)
	
	accounts = response.json()
	for account in accounts:
		if not frappe.db.exists('Bank Account', account["accountName"] + " - " + bank_of_cyprus.bank):
			new_account = frappe.get_doc({
				'doctype': 'Account',
				'account_name': account["accountName"],
				'parent_account': bank_of_cyprus.parent_account,
				'account_type': 'Bank',
				'account_currency': account["currency"],
			})
			new_account.insert()

			bank_account = frappe.get_doc({
				'doctype': 'Bank Account',
				'account_name': account["accountName"],
				'account': new_account.name,
				'is_company_account': True,
				'bank': bank_of_cyprus.bank,
				'bank_account_no': account["accountId"],
				'currency': account["currency"],
				#'iban': account["IBAN"],
			})
			bank_account.insert()
			frappe.db.set_value('Bank Account', bank_account.name, 'iban', account["IBAN"])
			
	return accounts

@frappe.whitelist()
def get_bank_transactions(bank_account, bank_statement_from_date, bank_statement_to_date):

	dateFrom = datetime.strptime(bank_statement_from_date, '%Y-%m-%d').strftime('%d/%m/%Y')
	dateTo = datetime.strptime(bank_statement_to_date, '%Y-%m-%d').strftime('%d/%m/%Y')

	bank_of_cyprus = frappe.get_doc("Bank Of Cyprus")
	bank_account_doc = frappe.get_doc("Bank Account", bank_account)
	access_token_1 = json.loads(bank_of_cyprus.access_token_1)
	subscription_id = json.loads(bank_of_cyprus.subscription_id)
	url = get_base_url(bank_of_cyprus) + "/v1/accounts/" + bank_account_doc.bank_account_no + "/statement"
	payload = {
		"startDate": dateFrom,
		"endDate": dateTo,
	}
	headers = {
		"Content-Type": "application/json",
		"Authorization": "Bearer " + access_token_1["access_token"],
		"subscriptionId": subscription_id["subscriptionId"],
		"originUserId": bank_of_cyprus.user_id,
		"journeyId": str(uuid.uuid4()),
		"timeStamp": datetime.utcnow().isoformat()
	}

	response = requests.get(url, params=payload, headers=headers)
	response_json = response.json()
	if (response.status_code != 200):
		frappe.throw(response.text)

	transactions = response_json["transaction"]
	for transaction in transactions:
		valueDate = datetime.strptime(transaction["valueDate"], '%d/%m/%Y').strftime('%Y-%m-%d')
		filters = {
			'date': valueDate,
			'reference_number': transaction["id"]
		}
		amount = transaction["transactionAmount"]["amount"]
		if transaction["dcInd"] == "CREDIT":
			filters["deposit"] = abs(amount)
		else:
			filters["withdrawal"] = abs(amount)
		existing = frappe.db.get_list('Bank Transaction', filters=filters)

		if (len(existing) == 0):
			bank_transaction = frappe.get_doc({
				"doctype": "Bank Transaction",
				"bank_account": bank_account,
				"status": "Pending",
				"date": valueDate,
				"reference_number": transaction["id"],
				"description": transaction["description"],
			})
			if transaction["dcInd"] == "CREDIT":
				bank_transaction.deposit = abs(amount)
			else:
				bank_transaction.withdrawal = abs(amount)

			bank_transaction.insert()
			bank_transaction.submit()
			
	return response_json
