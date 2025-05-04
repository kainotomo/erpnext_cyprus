import frappe
from frappe import _
import json
from erpnext.setup.doctype.company.company import Company
from erpnext.setup.setup_wizard.operations.taxes_setup import setup_taxes_and_charges, from_detailed_data, update_regional_tax_settings

class CustomCompany(Company):
	@frappe.whitelist()
	def create_default_tax_template(self):

		company_name = self.name
		country = frappe.db.get_value("Company", company_name, "country")
		
		# Regular setup for other countries
		if country != "Cyprus":
			setup_taxes_and_charges(company_name, country)
			return
		
		sales_tax_templates = [
			{
				"title": "Standard Domestic",
				"description": "For local sales with standard VAT.",
				"taxes": [
					{
						"account_head": {
							"account_name": "VAT",
							"account_number": "2320",
							"root_type": "Liability",
							"tax_rate": 19
						},
						"description": "Standard Domestic VAT",
						"charge_type": "On Net Total",
						"rate": 19
					}
				]
			},
			{
				"title": "Zero-Rated",
				"description": "For export sales where VAT is not charged.",
				"taxes": []
			},
			{
				"title": "Out-of-Scope",
				"description": "For sales out of scope of VAT.",
				"taxes": []
			}
		]      

		eu_vat_rates = get_eu_vat_rates()
		for country, vat_rate in eu_vat_rates.items():
			# Skip Cyprus as it uses domestic templates
			oss_template = {
				"title": f"OSS Digital Services - {country} ({vat_rate}%)",
				"description": f"Digital services to consumers in {country} (OSS)",
				"taxes": [
					{
						"account_head": {
							"account_name": "VAT OSS",
							"account_number": "2321",
							"root_type": "Liability",
							"tax_rate": 20.00
						},
						"description": f"VAT OSS {country} {vat_rate}%",
						"charge_type": "On Net Total",
						"rate": vat_rate
					}
				]
			}
			
			sales_tax_templates.append(oss_template)
		
		# Custom setup for Cyprus
		cyprus_tax_templates = {
			"chart_of_accounts": {
				"*": {
					"sales_tax_templates": sales_tax_templates,
					"purchase_tax_templates": [
						{
							"title": "Reverse Charge",
							"description": "Purchases eligible for reverse charge VAT",
							"taxes": [
								{
									"account_head": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"charge_type": "On Net Total",
									"rate": 19,
									"add_deduct_tax": "Add"
								},
								{
									"account_head": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"charge_type": "On Net Total",
									"rate": 19,
									"add_deduct_tax": "Deduct"
								}
							]
						},
						{
							"title": "Zero-Rated",
							"description": "For zero-rated or exempt purchases",
							"taxes": []
						},
						{
							"title": "Standard Domestic",
							"description": "For ordinary purchases from local (Cypriot) suppliers where the supplier charges VAT at the standard rate",
							"taxes": [
								{
									"account_head": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"description": "Standard Domestic",
									"rate": 19,
									"add_deduct_tax": "Add"
								}
							]
						}
					],
					"item_tax_templates": [
						{
							"title": "Cyprus Standard",
							"taxes": [
								{
									"tax_type": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 19
								}
							]
						},
						{
							"title": "Cyprus Reduced",
							"taxes": [
								{
									"tax_type": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 9
								}
							]
						},
						{
							"title": "Cyprus Super Reduced",
							"taxes": [
								{
									"tax_type": {
										"account_name": "VAT",
										"account_number": "2320",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 5
								}
							]
						}
					]
				}
			}
		}
		
		from_detailed_data(company_name, cyprus_tax_templates)
		update_regional_tax_settings("Cyprus", company_name)
		setup_tax_rules(company_name)
		make_salary_components(company_name)
	
	def create_default_accounts(self):
		if self.country == "Cyprus":
			self.chart_of_accounts = cyprus_coa()
		super().create_default_accounts()

def get_eu_vat_rates():
	"""
	Return a dictionary of EU country standard VAT rates for OSS
	Source: European Commission, rates as of 2023
	"""
	return {
		"Austria": 20,
		"Belgium": 21,
		"Bulgaria": 20,
		"Croatia": 25,
		"Czech Republic": 21,
		"Denmark": 25,
		"Estonia": 22,
		"Finland": 24,
		"France": 20,
		"Germany": 19,
		"Greece": 24,
		"Hungary": 27,
		"Ireland": 23,
		"Italy": 22,
		"Latvia": 21,
		"Lithuania": 21,
		"Luxembourg": 17,
		"Malta": 18,
		"Netherlands": 21,
		"Poland": 23,
		"Portugal": 23,
		"Romania": 19,
		"Slovakia": 20,
		"Slovenia": 22,
		"Spain": 21,
		"Sweden": 25
	}

def get_eu_countries():
	"""Return a list of EU countries"""
	return list(get_eu_vat_rates().keys())

def setup_tax_rules(company):
	"""
	Set up Cyprus-specific tax rules for automatic tax template selection
	"""
	rules_created = []
	
	# Get the actual template names first (since they include company abbreviations)
	template_names = {}
	
	# Get sales tax templates
	sales_templates = frappe.get_all(
		"Sales Taxes and Charges Template",
		filters={"company": company},
		fields=["name", "title"]
	)
	for template in sales_templates:
		template_names[template.title] = template.name
	
	# Get purchase tax templates
	purchase_templates = frappe.get_all(
		"Purchase Taxes and Charges Template",
		filters={"company": company},
		fields=["name", "title"]
	)
	for template in purchase_templates:
		template_names[template.title] = template.name
	
	# Initialize tax rules list
	tax_rules = []
	
	# Get EU VAT rates to create country-specific digital services rules
	eu_vat_rates = get_eu_vat_rates()
	
	# First add individual country rules for digital services
	for country, vat_rate in eu_vat_rates.items():
		if country == "Cyprus":
			# For Cyprus, use the standard template
			continue
			
		template_title = f"OSS Digital Services - {country} ({vat_rate}%)"
		template_name = template_names.get(template_title)
		
		if template_name:
			rule = {
				"doctype": "Tax Rule",
				"tax_type": "Sales",
				"customer_group": "Individual", 
				"billing_country": country,
				"sales_tax_template": template_name,
				"priority": 2,
				"use_for_shopping_cart": 1
			}
			tax_rules.append(rule)
	
	# Then add the standard rules    
	standard_rules = [
		# Default domestic rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Sales",
			"billing_country": "Cyprus",
			"sales_tax_template": template_names.get("Standard Domestic"),
			"priority": 2,
			"use_for_shopping_cart": 1
		},
		# EU B2B and other countries
		{
			"doctype": "Tax Rule",
			"tax_type": "Sales",
			"sales_tax_template": template_names.get("Zero-Rated"),
			"priority": 1,
			"use_for_shopping_cart": 1
		},
		
		# PURCHASE RULES
		# Domestic purchases rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"billing_country": "Cyprus",
			"purchase_tax_template": template_names.get("Standard Domestic"),
			"priority": 3
		},
		# EU commercial services rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"billing_country": "EU",
			"purchase_tax_template": template_names.get("Reverse Charge"),
			"priority": 2
		},        
		# Zero-rated purchases are handled by the default template
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"purchase_tax_template": template_names.get("Zero-Rated"),
			"priority": 1,
			"use_for_shopping_cart": 1
		},
	]
	
	# Combine all rules
	tax_rules.extend(standard_rules)
	
	# Create each tax rule if it doesn't already exist
	for rule_data in tax_rules:
		# Add company to rule data
		rule_data["company"] = company
		
		# Check for existing rule with similar criteria
		filters = {
			"tax_type": rule_data["tax_type"],
			"company": company,
			"priority": rule_data["priority"]
		}
		
		if "billing_country" in rule_data:
			filters["billing_country"] = rule_data["billing_country"]
			
		if "customer_group" in rule_data:
			filters["customer_group"] = rule_data["customer_group"]
			
		existing_rule = frappe.db.exists("Tax Rule", filters)
		
		if not existing_rule:
			# Special handling for EU country group
			if rule_data.get("billing_country") == "EU":
				# Create rules for each EU country
				eu_countries = get_eu_countries()
				for country in eu_countries:
					country_rule = rule_data.copy()
					country_rule["billing_country"] = country
					
					# Create the rule
					try:
						new_rule = frappe.get_doc(country_rule)
						new_rule.insert()
						rules_created.append(f"{country_rule['tax_type']} - {country} - Priority {country_rule['priority']}")
						frappe.db.commit()
					except Exception as e:
						frappe.log_error(f"Error creating tax rule for {country}: {str(e)}")
			else:
				# Create the rule
				try:
					new_rule = frappe.get_doc(rule_data)
					new_rule.insert()
					rules_created.append(f"{rule_data['tax_type']} - {rule_data.get('billing_country', 'Any')} - Priority {rule_data['priority']}")
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Error creating tax rule: {str(e)}")
	
	return rules_created

def make_salary_components(company):
	company_abbr = frappe.get_value("Company", company, "abbr")

	account_accounts_payable = frappe.get_value('Account', {'account_name': 'Accounts Payable', 'company': company}, 'name')
	account_payroll_payable = frappe.get_value('Account', {'account_name': 'Payroll Payable', 'company': company}, 'name')
	account_income_tax = frappe.get_value('Account', {'account_name': 'Payroll Income Tax', 'company': company}, 'name')
	account_salary = frappe.get_value('Account', {'account_name': 'Salary', 'company': company}, 'name')
		
	if not account_income_tax:
		account = frappe.get_doc({
			"doctype": "Account",
			"account_name": "Payroll Income Tax",
			"account_number": "2121",
			"company": company,
			"root_type": "Liability",
			"is_group": 0,
			"report_type": "Balance Sheet",
			"parent_account": account_accounts_payable
		})
		account.insert(ignore_if_duplicate=True)
		account.submit()
		frappe.db.commit()
		account_income_tax = account.name
		

	docs = []

	file_path = frappe.get_app_path("erpnext_cyprus", "regional", "cyprus", "data", "salary_components.json")
	file_content = read_data_file(file_path)
	file_content = file_content.replace("ACCOUNT_SALARY", account_salary)
	file_content = file_content.replace("ACCOUNT_PAYROLL_PAYABLE", account_payroll_payable)
	file_content = file_content.replace("ACCOUNT_PAYROLL_INCOME_TAX", account_income_tax)
	file_content = file_content.replace("E2C_COMPANY", company)
	docs.extend(json.loads(file_content))

	for d in docs:
		try:
			doc = frappe.get_doc(d)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_if_duplicate=True)
		except frappe.NameError:
			frappe.clear_messages()
		except frappe.DuplicateEntryError:
			frappe.clear_messages()

def read_data_file(file_path):
	try:
		with open(file_path) as f:
			return f.read()
	except OSError:
		return "{}"
	
def cyprus_coa():
	return {
		_("Application of Funds (Assets)"): {
			_("Current Assets"): {
				_("Accounts Receivable"): {
					_("Debtors"): {"account_type": "Receivable", "account_number": "1310"},
					"account_number": "1300",
				},
				_("Bank Accounts"): {"account_type": "Bank", "is_group": 1, "account_number": "1200"},
				_("Cash In Hand"): {
					_("Cash"): {"account_type": "Cash", "account_number": "1110"},
					"account_type": "Cash",
					"account_number": "1100",
				},
				_("Loans and Advances (Assets)"): {
					_("Employee Advances"): {"account_number": "1610"},
					"account_number": "1600",
				},
				_("Securities and Deposits"): {
					_("Earnest Money"): {"account_number": "1651"},
					"account_number": "1650",
				},
				_("Stock Assets"): {
					_("Stock In Hand"): {"account_type": "Stock", "account_number": "1410"},
					"account_type": "Stock",
					"account_number": "1400",
				},
				_("Tax Assets"): {"is_group": 1, "account_number": "1500"},
				"account_number": "1100-1600",
			},
			_("Fixed Assets"): {
				_("Capital Equipments"): {"account_type": "Fixed Asset", "account_number": "1710"},
				_("Electronic Equipments"): {"account_type": "Fixed Asset", "account_number": "1720"},
				_("Furnitures and Fixtures"): {"account_type": "Fixed Asset", "account_number": "1730"},
				_("Office Equipments"): {"account_type": "Fixed Asset", "account_number": "1740"},
				_("Plants and Machineries"): {"account_type": "Fixed Asset", "account_number": "1750"},
				_("Buildings"): {"account_type": "Fixed Asset", "account_number": "1760"},
				_("Softwares"): {"account_type": "Fixed Asset", "account_number": "1770"},
				_("Accumulated Depreciation"): {
					"account_type": "Accumulated Depreciation",
					"account_number": "1780",
				},
				_("CWIP Account"): {"account_type": "Capital Work in Progress", "account_number": "1790"},
				"account_number": "1700",
			},
			_("Investments"): {"is_group": 1, "account_number": "1800"},
			_("Temporary Accounts"): {
				_("Temporary Opening"): {"account_type": "Temporary", "account_number": "1910"},
				"account_number": "1900",
			},
			"root_type": "Asset",
			"account_number": "1000",
		},
		_("Expenses"): {
			_("Direct Expenses"): {
				_("Stock Expenses"): {
					_("Cost of Goods Sold"): {"account_type": "Cost of Goods Sold", "account_number": "5111"},
					_("Expenses Included In Asset Valuation"): {
						"account_type": "Expenses Included In Asset Valuation",
						"account_number": "5112",
					},
					_("Expenses Included In Valuation"): {
						"account_type": "Expenses Included In Valuation",
						"account_number": "5118",
					},
					_("Stock Adjustment"): {"account_type": "Stock Adjustment", "account_number": "5119"},
					"account_number": "5110",
				},
				"account_number": "5100",
			},
			_("Indirect Expenses"): {
				_("Administrative Expenses"): {"account_number": "5201"},
				_("Commission on Sales"): {"account_number": "5202"},
				_("Depreciation"): {"account_type": "Depreciation", "account_number": "5203"},
				_("Entertainment Expenses"): {"account_number": "5204"},
				_("Freight and Forwarding Charges"): {"account_type": "Chargeable", "account_number": "5205"},
				_("Legal Expenses"): {"account_number": "5206"},
				_("Marketing Expenses"): {"account_type": "Chargeable", "account_number": "5207"},
				_("Office Maintenance Expenses"): {"account_number": "5208"},
				_("Office Rent"): {"account_number": "5209"},
				_("Postal Expenses"): {"account_number": "5210"},
				_("Print and Stationery"): {"account_number": "5211"},
				_("Round Off"): {"account_type": "Round Off", "account_number": "5212"},
				_("Salary"): {"account_number": "5213"},
				_("Sales Expenses"): {"account_number": "5214"},
				_("Telephone Expenses"): {"account_number": "5215"},
				_("Travel Expenses"): {"account_number": "5216"},
				_("Utility Expenses"): {"account_number": "5217"},
				_("Write Off"): {"account_number": "5218"},
				_("Exchange Gain/Loss"): {"account_number": "5219"},
				_("Gain/Loss on Asset Disposal"): {"account_number": "5220"},
				_("Miscellaneous Expenses"): {"account_type": "Chargeable", "account_number": "5221"},
				"account_number": "5200",
			},
			"root_type": "Expense",
			"account_number": "5000",
		},
		_("Income"): {
			_("Direct Income"): {
				_("Sales"): {"account_number": "4110"},
				_("Service"): {"account_number": "4120"},
				"account_number": "4100",
			},
			_("Indirect Income"): {"is_group": 1, "account_number": "4200"},
			"root_type": "Income",
			"account_number": "4000",
		},
		_("Source of Funds (Liabilities)"): {
			_("Current Liabilities"): {
				_("Accounts Payable"): {
					_("Creditors"): {"account_type": "Payable", "account_number": "2110"},
					_("Payroll Payable"): {"account_number": "2120"},
					"account_number": "2100",
				},
				_("Stock Liabilities"): {
					_("Stock Received But Not Billed"): {
						"account_type": "Stock Received But Not Billed",
						"account_number": "2210",
					},
					_("Asset Received But Not Billed"): {
						"account_type": "Asset Received But Not Billed",
						"account_number": "2211",
					},
					"account_number": "2200",
				},
				_("Duties and Taxes"): {
					_("TDS Payable"): {"account_number": "2310"},
					"account_type": "Tax",
					"is_group": 1,
					"account_number": "2300",
				},
				_("Loans (Liabilities)"): {
					_("Secured Loans"): {"account_number": "2410"},
					_("Unsecured Loans"): {"account_number": "2420"},
					_("Bank Overdraft Account"): {"account_number": "2430"},
					"account_number": "2400",
				},
				"account_number": "2100-2400",
			},
			"root_type": "Liability",
			"account_number": "2000",
		},
		_("Equity"): {
			_("Capital Stock"): {"account_type": "Equity", "account_number": "3100"},
			_("Dividends Paid"): {"account_type": "Equity", "account_number": "3200"},
			_("Opening Balance Equity"): {"account_type": "Equity", "account_number": "3300"},
			_("Retained Earnings"): {"account_type": "Equity", "account_number": "3400"},
			"root_type": "Equity",
			"account_number": "3000",
		},
	}
