import frappe
from erpnext.setup.doctype.company.company import Company
from erpnext.setup.setup_wizard.operations.taxes_setup import setup_taxes_and_charges, from_detailed_data

class CustomCompany(Company):
	@frappe.whitelist()
	def create_default_tax_template(self):

		company_name = self.name
		country = frappe.db.get_value("Company", company_name, "country")
		
		# Regular setup for other countries
		if country != "Cyprus":
			setup_taxes_and_charges(company_name, country)
			return
		
		# Custom setup for Cyprus
		cyprus_tax_templates = {
			"chart_of_accounts": {
				"*": {
					"sales_tax_templates": [
						{
							"title": "Standard Domestic",
							"description": "For local sales with standard VAT.",
							"taxes": [
								{
									"account_head": {
										"account_name": "VAT",
										"account_number": "2310",
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
					],
					"purchase_tax_templates": [
						{
							"title": "Reverse Charge",
							"description": "Purchases eligible for reverse charge VAT",
							"taxes": [
								{
									"account_head": "VAT",
									"charge_type": "On Net Total",
									"rate": 19,
									"add_deduct_tax": "Add"
								},
								{
									"account_head": "VAT",
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
									"account_head": "VAT",
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
									"tax_type": "VAT",
									"tax_rate": 19
								}
							]
						},
						{
							"title": "Cyprus Reduced",
							"taxes": [
								{
									"tax_type": "VAT",
									"tax_rate": 9
								}
							]
						},
						{
							"title": "Cyprus Super Reduced",
							"taxes": [
								{
									"tax_type": "VAT",
									"tax_rate": 5
								}
							]
						},
						{
							"title": "Zero Rated",
							"taxes": [
								{
									"tax_type": "VAT",
									"tax_rate": 0
								}
							]
						}
					]
				}
			}
		}
		
		frappe.msgprint("Applying Cyprus tax templates")
		from_detailed_data(company_name, cyprus_tax_templates)