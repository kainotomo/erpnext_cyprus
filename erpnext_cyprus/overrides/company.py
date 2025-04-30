import frappe
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
							"account_number": "2310",
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
							"account_number": "2320",
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
										"account_number": "2310",
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
										"account_number": "2310",
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
										"account_number": "2310",
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
										"account_number": "2310",
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
										"account_number": "2310",
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
										"account_number": "2310",
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
		update_regional_tax_settings(country, company_name)
		frappe.msgprint("Cyprus tax templates applied successfully")

	
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
