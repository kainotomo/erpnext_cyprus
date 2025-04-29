# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.utils.tax_utils import get_eu_countries

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return [
		{
			"fieldname": "vat_field",
			"label": _("Field"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "amount",
			"label": _("Amount (EUR)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		}
	]

def get_data(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	vat_account = filters.get("vat_account")
	vat_accounts = get_vat_accounts_from_filter(company, vat_account)
	if not company or not from_date or not to_date or not vat_account or not vat_accounts:
		return []
	
	# Initialize VAT return data
	vat_return_data = []
	
	# Add VAT Return fields according to Cyprus tax requirements
	# Box 1: VAT due on sales and other outputs
	output_vat = get_box_1(company, from_date, to_date, vat_accounts)
	vat_return_data.append({
		"vat_field": _("Box 1"),
		"description": _("VAT due on sales and other outputs"),
		"amount": output_vat
	})

	# Box 2: VAT due on acquisitions from EU countries
	eu_acquisitions_vat = get_box_2(company, from_date, to_date, vat_accounts)
	vat_return_data.append({
		"vat_field": _("Box 2"),
		"description": _("VAT due on acquisitions from EU countries"),
		"amount": eu_acquisitions_vat
	})
	
	# Box 3: Total VAT due (box 1 + box 2)
	total_vat_due = flt(output_vat) + flt(eu_acquisitions_vat)
	vat_return_data.append({
		"vat_field": _("Box 3"),
		"description": _("Total VAT due (sum of boxes 1 and 2)"),
		"amount": total_vat_due,
		"bold": 1
	})
	
	# Box 4: VAT reclaimed on purchases and other inputs
	input_vat = get_box_4(company, from_date, to_date, vat_accounts)
	vat_return_data.append({
		"vat_field": _("Box 4"),
		"description": _("VAT reclaimed on purchases and other inputs"),
		"amount": input_vat
	})
	
	# Box 5: Net VAT to be paid or reclaimed
	net_vat = flt(total_vat_due) - flt(input_vat)
	vat_return_data.append({
		"vat_field": _("Box 5"),
		"description": _("Net VAT to be paid or reclaimed"),
		"amount": net_vat,
		"bold": 1
	})
	
	# Box 6: Total value of sales and other outputs excluding VAT
	total_sales = get_box_6(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 6"),
		"description": _("Total value of sales and other outputs excluding VAT"),
		"amount": total_sales
	})
	
	# Box 7: Total value of purchases and inputs excluding VAT
	total_purchases = get_box_7(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 7"),
		"description": _("Total value of purchases and inputs excluding VAT"),
		"amount": total_purchases
	})
	
	# Box 8A & 8B: EU goods and services supplies
	eu_supplies_goods = get_box_8a(company, from_date, to_date)
	eu_supplies_services = get_box_8b(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 8A"),
		"description": _("Total value of supplies of goods to EU countries"),
		"amount": eu_supplies_goods
	})
	vat_return_data.append({
		"vat_field": _("Box 8B"),
		"description": _("Total value of supplies of services to EU countries"),
		"amount": eu_supplies_services
	})
	
	# Box 9: Total value of exports to non-EU countries
	non_eu_exports = get_box_9(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 9"),
		"description": _("Total value of exports to non-EU countries"),
		"amount": non_eu_exports
	})
	
	# Box 10: Total value of out-of-scope sales
	out_of_scope = get_box_10(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 10"),
		"description": _("Total value of out-of-scope sales"),
		"amount": out_of_scope
	})
	
	# Box 11A & 11B: EU goods and services acquisitions
	eu_acquisitions_goods = get_box_11a(company, from_date, to_date)
	eu_acquisitions_services = get_box_11b(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 11A"),
		"description": _("Total value of acquisitions of goods from EU countries"),
		"amount": eu_acquisitions_goods
	})
	vat_return_data.append({
		"vat_field": _("Box 11B"),
		"description": _("Total value of acquisitions of services from EU countries"),
		"amount": eu_acquisitions_services
	})
	
	return vat_return_data

def get_box_1(company, from_date, to_date, vat_accounts):
	
	# Format for SQL IN clause - converting to a proper list of parameters
	placeholder_list = ', '.join(['%s'] * len(vat_accounts))
	
	# Query for VAT due on sales
	query = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Sales Invoice' THEN gle.credit
				WHEN gle.voucher_subtype = 'Credit Note' THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		LEFT JOIN `tabSales Invoice` pi ON gle.voucher_no = pi.name AND gle.voucher_type = 'Sales Invoice'
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account IN ({0})
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + vat_accounts
	
	# Execute query
	output_vat_result = frappe.db.sql(query, params, as_dict=1)
	output_vat = flt(output_vat_result[0].vat_amount) if output_vat_result and output_vat_result[0].vat_amount is not None else 0
	
	return output_vat

def get_box_2(company, from_date, to_date, vat_accounts):
	
	# Format for SQL IN clause - converting to a proper list of parameters
	placeholder_list = ', '.join(['%s'] * len(vat_accounts))
	
	# Query for VAT due on acquisitions, handling Debit Notes differently
	query = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Purchase Invoice' THEN gle.credit
				WHEN gle.voucher_subtype = 'Debit Note' THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		LEFT JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name AND gle.voucher_type = 'Purchase Invoice'
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account IN ({0})
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + vat_accounts
	
	# Execute query
	output_vat_result = frappe.db.sql(query, params, as_dict=1)
	output_vat = flt(output_vat_result[0].vat_amount) if output_vat_result and output_vat_result[0].vat_amount is not None else 0
	
	return output_vat

def get_box_4(company, from_date, to_date, vat_accounts):
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(vat_accounts))
	
	# Query for Sales Invoices - reverse of Box 1
	query1 = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Sales Invoice' THEN gle.debit
				WHEN gle.voucher_subtype = 'Credit Note' THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account IN ({0})
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
	""".format(placeholder_list)
	
	params1 = [from_date, to_date, company] + vat_accounts
	sales_vat_result = frappe.db.sql(query1, params1, as_dict=1)
	sales_vat = flt(sales_vat_result[0].vat_amount) if sales_vat_result and sales_vat_result[0].vat_amount is not None else 0
	
	# Query for Purchase Invoices - reverse of Box 2
	query2 = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Purchase Invoice' THEN gle.debit
				WHEN gle.voucher_subtype = 'Debit Note' THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account IN ({0})
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
	""".format(placeholder_list)
	
	params2 = [from_date, to_date, company] + vat_accounts
	purchase_vat_result = frappe.db.sql(query2, params2, as_dict=1)
	purchase_vat = flt(purchase_vat_result[0].vat_amount) if purchase_vat_result and purchase_vat_result[0].vat_amount is not None else 0
	
	# Combine both VAT components
	return sales_vat + purchase_vat

def get_box_6(company, from_date, to_date):
	# Part 1: Get regular sales excluding VAT directly from Sales Invoice table
	sales_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabSales Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
	"""
	
	# Execute query for sales invoices
	sales_result = frappe.db.sql(sales_query, [from_date, to_date, company], as_dict=1)
	total_sales = flt(sales_result[0].amount) if sales_result and sales_result[0].amount is not None else 0
	
	# Part 2: Include Purchase Invoices with specific tax templates
	# Get company abbreviation to match template names
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	# Template patterns to search for
	special_templates = [
		f"Reverse Charge - {company_abbr}"
	]
	
	template_placeholders = ', '.join(['%s'] * len(special_templates))
	
	purchase_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabPurchase Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND taxes_and_charges IN ({0})
		AND docstatus = 1
	""".format(template_placeholders)
	
	# Execute query for purchase invoices with special templates
	purchase_params = [from_date, to_date, company] + special_templates
	purchase_result = frappe.db.sql(purchase_query, purchase_params, as_dict=1)
	special_purchase_amount = flt(purchase_result[0].amount) if purchase_result and purchase_result[0].amount is not None else 0
	
	# Combine both components
	return total_sales + special_purchase_amount

def get_box_7(company, from_date, to_date):
	# Get total purchases excluding VAT directly from Purchase Invoice table
	purchase_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabPurchase Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
	"""
	
	# Execute query
	purchase_result = frappe.db.sql(purchase_query, [from_date, to_date, company], as_dict=1)
	total_purchases = flt(purchase_result[0].amount) if purchase_result and purchase_result[0].amount is not None else 0
	
	return total_purchases

def get_box_8a(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list - add EU countries to the parameters
	params = [from_date, to_date, company] + eu_countries
	
	eu_goods = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_box_8b(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country IN ({0})
		AND item.custom_is_service = 1
	""".format(placeholder_list)
	
	# Build parameters list - add EU countries to the parameters
	params = [from_date, to_date, company] + eu_countries
	
	eu_services = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_box_9(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country != "Cyprus"
		AND addr.country NOT IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	non_eu_exports = frappe.db.sql(query, params, as_dict=1)
	
	return flt(non_eu_exports[0].amount) if non_eu_exports and non_eu_exports[0].amount is not None else 0

def get_box_10(company, from_date, to_date):
	# Get company abbreviation to match template names
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	# Out of scope template
	out_of_scope_templates = [
		f"Out-of-Scope - {company_abbr}"
	]
	
	# Format for SQL IN clause
	template_placeholders = ', '.join(['%s'] * len(out_of_scope_templates))
	
	query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabSales Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
		AND taxes_and_charges IN ({0})
	""".format(template_placeholders)
	
	# Build parameters list
	params = [from_date, to_date, company] + out_of_scope_templates
	
	# Execute query
	out_of_scope = frappe.db.sql(query, params, as_dict=1)
	
	# Return result
	return flt(out_of_scope[0].amount) if out_of_scope and out_of_scope[0].amount is not None else 0

def get_box_11a(company, from_date, to_date):
	# Get EU countries list
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	# Build query for goods (non-services) from EU countries
	query = """
		SELECT SUM(pii.base_net_amount) as amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabAddress` addr ON pi.supplier_address = addr.name
		LEFT JOIN `tabItem` item ON pii.item_code = item.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND addr.country IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	eu_goods = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_box_11b(company, from_date, to_date):
	# Get EU countries list
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	# Build query using same pattern as get_box_8b but for purchase invoices
	query = """
		SELECT SUM(pii.base_net_amount) as amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabAddress` addr ON pi.supplier_address = addr.name
		LEFT JOIN `tabItem` item ON pii.item_code = item.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND addr.country IN ({0})
		AND item.custom_is_service = 1
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	eu_services = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_vat_accounts_from_filter(company, vat_account):
	"""
	Get all tax accounts that are children of the selected vat_account
	and have account_type = 'Tax'
	
	Parameters:
	- company (str): Company for which to fetch accounts
	- vat_account (str): Parent VAT account selected by user
	
	Returns:
	- list: List of account names
	"""
	accounts = []
	
	# Check if selected account itself has account_type = 'Tax'
	account_type = frappe.db.get_value("Account", vat_account, "account_type")
	is_group = frappe.db.get_value("Account", vat_account, "is_group")
	
	if account_type == "Tax":
		accounts.append(vat_account)
	
	# If the selected account is a group account, get its children with account_type = 'Tax'
	if is_group:
		children = frappe.db.sql("""
			SELECT name
			FROM `tabAccount`
			WHERE parent_account = %s
			AND company = %s
			AND account_type = 'Tax'
		""", (vat_account, company), as_dict=1)
		
		# Add all child tax accounts to the list
		for child in children:
			accounts.append(child.name)
	
	return accounts
