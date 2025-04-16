import frappe
from frappe import _
from frappe.model.document import Document
import datetime
from frappe.utils import nowdate, add_days, getdate
from frappe.utils.data import flt, cstr

@frappe.whitelist()
def create_sample_data(company):
	"""
	Create sample data for the given company. Covers Cyprus, EU, and Non-EU cases for customers, suppliers, and transactions.
	"""

	create_customers(company)
	create_suppliers(company)
	create_items(company)
	create_sales_invoices(company)
	
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
	
	frappe.db.commit()

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
	
	frappe.db.commit()

def create_items(company):
	"""
	Create sample items for all tax scenarios in Cyprus
	"""
	# Create Digital Services item group if it doesn't exist
	if not frappe.db.exists("Item Group", "Digital Services"):
		digital_group = frappe.new_doc("Item Group")
		digital_group.item_group_name = "Digital Services"
		digital_group.parent_item_group = "All Item Groups"
		digital_group.save()
	
	# Create sample items
	items = [
		{
			"item_code": "CY-STD-ITEM",
			"item_name": "Cyprus Standard Rate Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 100,
			"income_account": "Goods - Standard Rate (19%) - " + company,
			"description": "Product taxed at standard rate (19%)"
		},
		{
			"item_code": "CY-RED9-ITEM",
			"item_name": "Cyprus Reduced Rate 9% Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 50,
			"income_account": "Goods - Reduced Rate (9%) - " + company,
			"description": "Product taxed at reduced rate (9%)"
		},
		{
			"item_code": "CY-RED5-ITEM",
			"item_name": "Cyprus Reduced Rate 5% Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 40,
			"income_account": "Goods - Reduced Rate (5%) - " + company,
			"description": "Product taxed at reduced rate (5%)"
		},
		{
			"item_code": "CY-ZERO-ITEM",
			"item_name": "Cyprus Zero Rated Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 75,
			"income_account": "Goods - Zero Rate - " + company,
			"description": "Zero-rated product"
		},
		{
			"item_code": "CY-EXEMPT-ITEM",
			"item_name": "Cyprus Exempt Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 60,
			"income_account": "Goods - Exempt - " + company,
			"description": "Exempt product"
		},
		{
			"item_code": "EU-GOODS-ITEM",
			"item_name": "EU Goods Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 120,
			"income_account": "EU Sales - Goods B2B - " + company,
			"description": "Goods for EU customers"
		},
		{
			"item_code": "EU-SERVICE-ITEM",
			"item_name": "EU Services Item",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 150,
			"income_account": "EU Sales - Services B2B - " + company,
			"description": "Services for EU customers"
		},
		{
			"item_code": "NON-EU-GOODS-ITEM",
			"item_name": "Non-EU Goods Item",
			"item_group": "Products",
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"standard_rate": 130,
			"income_account": "Non-EU Exports - Goods - " + company,
			"description": "Goods for Non-EU customers"
		},
		{
			"item_code": "NON-EU-SERVICE-ITEM",
			"item_name": "Non-EU Services Item",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 160,
			"income_account": "Non-EU Services - " + company,
			"description": "Services for Non-EU customers"
		},
		{
			"item_code": "EU-DIGITAL-ITEM",
			"item_name": "EU Digital Services Item",
			"item_group": "Digital Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 25,
			"income_account": "Digital Services - EU B2C - " + company,
			"description": "Digital services for EU B2C customers (OSS scheme)"
		},
		{
			"item_code": "CY-SERVICE-STD",
			"item_name": "Cyprus Standard Rate Service",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 200,
			"income_account": "Services - Standard Rate (19%) - " + company,
			"description": "Service taxed at standard rate (19%)"
		},
		{
			"item_code": "CY-SERVICE-RED9",
			"item_name": "Cyprus Reduced Rate 9% Service",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 100,
			"income_account": "Services - Reduced Rate (9%) - " + company,
			"description": "Service taxed at reduced rate (9%)"
		},
		{
			"item_code": "CY-SERVICE-RED5",
			"item_name": "Cyprus Reduced Rate 5% Service",
			"item_group": "Services",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"standard_rate": 80,
			"income_account": "Services - Reduced Rate (5%) - " + company,
			"description": "Service taxed at reduced rate (5%)"
		}
	]
	
	for item in items:
		if not frappe.db.exists("Item", item["item_code"]):
			doc = frappe.get_doc({
				"doctype": "Item",
				"item_code": item["item_code"],
				"item_name": item["item_name"],
				"item_group": item["item_group"],
				"stock_uom": item["stock_uom"],
				"is_stock_item": item["is_stock_item"],
				"standard_rate": item["standard_rate"],
				"description": item["description"],
				"income_account": item["income_account"]
			})
			doc.insert(ignore_permissions=True)
	
	frappe.db.commit()

def create_sales_invoices(company):
	"""
	Create sample sales invoices covering all Cyprus tax scenarios
	"""
	# Set posting date in the current month for reporting
	posting_date = nowdate()
	
	# 1. Domestic Sales with Standard Rate (19%)
	create_sales_invoice(
		title="Cyprus B2B Standard Rate Invoice",
		customer="Cyprus B2B Customer",
		items=[
			{"item_code": "CY-STD-ITEM", "qty": 2, "rate": 100}
		],
		posting_date=posting_date,
		company=company
	)
	
	create_sales_invoice(
		title="Cyprus B2C Standard Rate Invoice",
		customer="Cyprus B2C Customer",
		items=[
			{"item_code": "CY-STD-ITEM", "qty": 1, "rate": 100},
			{"item_code": "CY-SERVICE-STD", "qty": 1, "rate": 200}
		],
		posting_date=posting_date,
		company=company
	)
	
	# 2. Domestic Sales with Reduced Rates
	create_sales_invoice(
		title="Cyprus Reduced Rate 9% Invoice",
		customer="Cyprus B2B Customer",
		items=[
			{"item_code": "CY-RED9-ITEM", "qty": 3, "rate": 50},
			{"item_code": "CY-SERVICE-RED9", "qty": 1, "rate": 100}
		],
		posting_date=add_days(posting_date, 1),
		company=company
	)
	
	create_sales_invoice(
		title="Cyprus Reduced Rate 5% Invoice",
		customer="Cyprus B2C Customer",
		items=[
			{"item_code": "CY-RED5-ITEM", "qty": 2, "rate": 40},
			{"item_code": "CY-SERVICE-RED5", "qty": 1, "rate": 80}
		],
		posting_date=add_days(posting_date, 1),
		company=company
	)
	
	# 3. Zero-rated and Exempt Sales
	create_sales_invoice(
		title="Cyprus Zero Rated Invoice",
		customer="Cyprus Zero Rated Customer",
		items=[
			{"item_code": "CY-ZERO-ITEM", "qty": 4, "rate": 75}
		],
		posting_date=add_days(posting_date, 2),
		company=company
	)
	
	create_sales_invoice(
		title="Cyprus Exempt Invoice",
		customer="Cyprus Exempt Customer",
		items=[
			{"item_code": "CY-EXEMPT-ITEM", "qty": 1, "rate": 60}
		],
		posting_date=add_days(posting_date, 2),
		company=company
	)
	
	# 4. EU Sales - Goods
	create_sales_invoice(
		title="EU B2B Goods Invoice",
		customer="EU B2B Customer",
		items=[
			{"item_code": "EU-GOODS-ITEM", "qty": 2, "rate": 120}
		],
		posting_date=add_days(posting_date, 3),
		company=company
	)
	
	create_sales_invoice(
		title="EU B2C Goods Invoice",
		customer="EU B2C Customer",
		items=[
			{"item_code": "EU-GOODS-ITEM", "qty": 1, "rate": 120}
		],
		posting_date=add_days(posting_date, 3),
		company=company
	)
	
	# 5. EU Sales - Services
	create_sales_invoice(
		title="EU B2B Services Invoice",
		customer="EU B2B Customer",
		items=[
			{"item_code": "EU-SERVICE-ITEM", "qty": 1, "rate": 150}
		],
		posting_date=add_days(posting_date, 4),
		company=company
	)
	
	# 6. Digital Services - OSS
	create_sales_invoice(
		title="EU OSS Digital Services Invoice",
		customer="EU OSS Digital Services Customer",
		items=[
			{"item_code": "EU-DIGITAL-ITEM", "qty": 4, "rate": 25}
		],
		posting_date=add_days(posting_date, 4),
		company=company
	)
	
	# 7. Non-EU Sales
	create_sales_invoice(
		title="Non-EU B2B Goods Export Invoice",
		customer="Non-EU B2B Customer",
		items=[
			{"item_code": "NON-EU-GOODS-ITEM", "qty": 3, "rate": 130}
		],
		posting_date=add_days(posting_date, 5),
		company=company
	)
	
	create_sales_invoice(
		title="Non-EU B2C Services Invoice",
		customer="Non-EU B2C Customer",
		items=[
			{"item_code": "NON-EU-SERVICE-ITEM", "qty": 1, "rate": 160}
		],
		posting_date=add_days(posting_date, 5),
		company=company
	)
	
	# 8. Mixed tax rates invoice
	create_sales_invoice(
		title="Mixed Tax Rates Invoice",
		customer="Cyprus B2B Customer",
		items=[
			{"item_code": "CY-STD-ITEM", "qty": 1, "rate": 100},
			{"item_code": "CY-RED9-ITEM", "qty": 1, "rate": 50},
			{"item_code": "CY-RED5-ITEM", "qty": 1, "rate": 40}
		],
		posting_date=add_days(posting_date, 6),
		company=company
	)

def create_sales_invoice(title, customer, items, posting_date, company):
	"""
	Helper function to create a sales invoice
	"""
	if frappe.db.exists("Sales Invoice", {"title": title, "company": company}):
		return
	
	# Get customer document
	customer_doc = frappe.get_doc("Customer", {"customer_name": customer})
	
	# Create invoice doc
	invoice = frappe.new_doc("Sales Invoice")
	invoice.title = title
	invoice.customer = customer_doc.name
	invoice.company = company
	invoice.posting_date = posting_date
	invoice.due_date = add_days(posting_date, 30)
	invoice.set_posting_time = 1
	invoice.update_stock = 0
	invoice.customer_group = customer_doc.customer_group
	invoice.territory = "All Territories"
	
	# Add items to invoice
	for item in items:
		invoice.append("items", {
			"item_code": item["item_code"],
			"qty": item["qty"],
			"rate": item["rate"]
		})
	
	# Save and submit
	try:
		invoice.set_taxes()
		invoice.insert(ignore_permissions=True)
		invoice.submit()
		frappe.db.commit()
	except Exception as e:
		frappe.log_error(f"Failed to create invoice {title}: {str(e)}")
		frappe.db.rollback()

@frappe.whitelist()
def delete_sample_data(company):
	"""
	Delete sample data for the given company. This includes items, sales invoices, customers and suppliers.
	"""
	# Delete in the correct order to avoid reference issues
	delete_sales_invoices(company)
	delete_items(company)
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

def delete_items(company):
	item_codes = [
		"CY-STD-ITEM",
		"CY-RED9-ITEM",
		"CY-RED5-ITEM",
		"CY-ZERO-ITEM",
		"CY-EXEMPT-ITEM",
		"EU-GOODS-ITEM",
		"EU-SERVICE-ITEM",
		"NON-EU-GOODS-ITEM",
		"NON-EU-SERVICE-ITEM",
		"EU-DIGITAL-ITEM",
		"CY-SERVICE-STD",
		"CY-SERVICE-RED9",
		"CY-SERVICE-RED5"
	]

	for item_code in item_codes:
		try:
			# First check if item exists
			if frappe.db.exists("Item", item_code):
				# Check if any documents reference this item before trying to delete
				if not frappe.db.exists("Sales Invoice Item", {"item_code": item_code, "docstatus": 1}):
					frappe.delete_doc("Item", item_code, force=1)
		except Exception as e:
			frappe.log_error(f"Failed to delete item {item_code}: {str(e)}")

def delete_sales_invoices(company):
	try:
		# Get all submitted sales invoices for the company
		invoices = frappe.get_all("Sales Invoice", 
			filters={"company": company, "docstatus": 1},
			pluck="name")
		
		# Cancel and delete each invoice
		for invoice in invoices:
			if frappe.db.exists("Sales Invoice", invoice):
				doc = frappe.get_doc("Sales Invoice", invoice)
				if doc.docstatus == 1:
					doc.cancel()
				frappe.delete_doc("Sales Invoice", invoice)
	except Exception as e:
		frappe.log_error(f"Failed to delete sales invoices for company {company}: {str(e)}")
