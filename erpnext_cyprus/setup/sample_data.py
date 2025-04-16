import frappe
from frappe import _
from frappe.model.document import Document

@frappe.whitelist()
def create_sample_data(company):
	"""
	Create sample data for the given company. Covers Cyprus, EU, and Non-EU cases for customers, suppliers, and transactions.
	"""

	create_customers(company)
	create_suppliers(company)
	
	return {"message": "Sample data created successfully"}

def create_customers(company):
	customers = [
		{
			"customer_name": "Cyprus B2B Customer",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"country": "Cyprus",
			"tax_id": "CY10340430X",
			"company": company
		},
		{
			"customer_name": "Cyprus B2C Customer",
			"customer_type": "Individual",
			"customer_group": "Individual",
			"country": "Cyprus",
			"company": company
		},
		{
			"customer_name": "Cyprus Exempt Customer",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"country": "Cyprus",
			"tax_id": "CY95812374L",
			"company": company
		},
		{
			"customer_name": "Cyprus Zero Rated Customer",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"country": "Cyprus",
			"tax_id": "CY76549312M",
			"company": company
		},
		{
			"customer_name": "EU B2B Customer",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"country": "Germany",
			"tax_id": "DE813164483",
			"company": company
		},
		{
			"customer_name": "EU B2C Customer",
			"customer_type": "Individual",
			"customer_group": "Individual",
			"country": "France",
			"company": company
		},
		{
			"customer_name": "EU OSS Digital Services Customer",
			"customer_type": "Individual",
			"customer_group": "Individual",
			"country": "Spain",
			"company": company
		},
		{
			"customer_name": "Non-EU B2B Customer",
			"customer_type": "Company",
			"customer_group": "Commercial",
			"country": "United States",
			"tax_id": "US12-3456789",
			"company": company
		},
		{
			"customer_name": "Non-EU B2C Customer",
			"customer_type": "Individual",
			"customer_group": "Individual",
			"country": "Australia",
			"company": company
		}
	]
	for cust in customers:
		if not frappe.db.exists("Customer", {"customer_name": cust["customer_name"]}):
			doc = frappe.get_doc({
				"doctype": "Customer",
				**cust
			})
			doc.insert(ignore_permissions=True)

def create_suppliers(company):
	suppliers = [
		{
			"supplier_name": "Cyprus Supplier",
			"supplier_type": "Company",
			"country": "Cyprus",
			"tax_id": "CY87654321B"
		},
		{
			"supplier_name": "Cyprus Exempt Supplier",
			"supplier_type": "Company",
			"country": "Cyprus",
			"tax_id": "CY98765432C"
		},
		{
			"supplier_name": "Cyprus Reduced Rate Supplier",
			"supplier_type": "Company",
			"country": "Cyprus",
			"tax_id": "CY95162738D"
		},
		{
			"supplier_name": "EU Supplier - Germany",
			"supplier_type": "Company",
			"country": "Germany",
			"tax_id": "DE987654321"
		},
		{
			"supplier_name": "EU Supplier - France",
			"supplier_type": "Company",
			"country": "France",
			"tax_id": "FR12345678901"
		},
		{
			"supplier_name": "Non-EU Supplier",
			"supplier_type": "Company",
			"country": "United States",
			"tax_id": "US98-7654321"
		}
	]
	for supp in suppliers:
		if not frappe.db.exists("Supplier", {"supplier_name": supp["supplier_name"]}):
			doc = frappe.get_doc({
				"doctype": "Supplier",
				**supp
			})
			doc.insert(ignore_permissions=True)

@frappe.whitelist()
def delete_sample_data(company):
	"""
	Delete sample data for the given company. This includes customers and suppliers.
	"""
	# Delete customers and suppliers
	delete_customers(company)
	delete_suppliers(company)

	return {"message": "Sample data deleted successfully"}

def delete_customers(company):
	customer_names = [
		"Cyprus B2B Customer",
		"Cyprus B2C Customer",
		"Cyprus Exempt Customer",
		"Cyprus Zero Rated Customer",
		"EU B2B Customer",
		"EU B2C Customer",
		"EU OSS Digital Services Customer",
		"Non-EU B2B Customer",
		"Non-EU B2C Customer"
	]

	# Delete customers
	for customer_name in customer_names:
		try:
			frappe.db.delete("Customer", {"customer_name": customer_name})
		except Exception as e:
			frappe.log_error(f"Failed to delete customer {customer_name}: {str(e)}")

def delete_suppliers(company):
	supplier_names = [
		"Cyprus Supplier",
		"Cyprus Exempt Supplier",
		"Cyprus Reduced Rate Supplier",
		"EU Supplier - Germany",
		"EU Supplier - France",
		"Non-EU Supplier"
	]

	for supplier_name in supplier_names:
		try:
			frappe.db.delete("Supplier", {"supplier_name": supplier_name})
		except Exception as e:
			frappe.log_error(f"Failed to delete supplier {supplier_name}: {str(e)}")
