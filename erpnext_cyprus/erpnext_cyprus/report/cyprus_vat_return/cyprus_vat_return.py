# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.overrides.company import get_eu_countries

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
	output_vat_account = filters.get("output_vat_account")
	input_vat_account = filters.get("input_vat_account")
	
	if not company or not from_date or not to_date or not output_vat_account or not input_vat_account:
		return []
	
	# Initialize VAT return data
	vat_return_data = []
	
	# Add VAT Return fields according to Cyprus tax requirements
	# Box 1: VAT due on sales and other outputs
	output_vat = get_box_1(company, from_date, to_date, output_vat_account)
	vat_return_data.append({
		"vat_field": _("Box 1"),
		"description": _("VAT due on sales and other outputs"),
		"amount": output_vat
	})

	# Box 2: VAT due on acquisitions from EU countries
	eu_acquisitions_vat = get_box_2(company, from_date, to_date, output_vat_account)
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
	input_vat = get_box_4(company, from_date, to_date, input_vat_account)
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

def get_box_1(company, from_date, to_date, output_vat_account):
	"""
	Box 1: VAT due on sales and other outputs
	This function calculates the total Output VAT collected on sales transactions,
	properly accounting for refunds via Credit Notes.
	
	Parameters:
	- company (str): Company for which to calculate VAT
	- from_date (str): Start date for the calculation period
	- to_date (str): End date for the calculation period
	- output_vat_account (str): Output VAT account to use for calculation
	
	Returns:
	- float: Total Output VAT amount (net of refunds)
	"""
	# Query for Output VAT from Sales Invoices (credits to the Output VAT account)
	sales_vat_query = """
		SELECT SUM(
			CASE 
				WHEN gle.credit > 0 THEN gle.credit
				WHEN gle.debit < 0 THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
	"""
	
	# Execute query for Sales Invoices
	sales_vat_result = frappe.db.sql(sales_vat_query, [from_date, to_date, company, output_vat_account], as_dict=1)
	sales_vat = flt(sales_vat_result[0].vat_amount) if sales_vat_result and sales_vat_result[0].vat_amount is not None else 0
	
	# Query for Output VAT refunds from Credit Notes (debits to the Output VAT account)
	credit_note_query = """
		SELECT SUM(
			CASE 
				WHEN gle.debit > 0 THEN gle.debit
				WHEN gle.credit < 0 THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
		AND gle.voucher_no IN (
			SELECT name 
			FROM `tabSales Invoice` 
			WHERE is_return = 1 
			AND posting_date BETWEEN %s AND %s
			AND company = %s
			AND docstatus = 1
		)
	"""
	
	# Execute query for Credit Notes
	cn_vat_result = frappe.db.sql(credit_note_query, [from_date, to_date, company, output_vat_account, from_date, to_date, company], as_dict=1)
	cn_vat = flt(cn_vat_result[0].vat_amount) if cn_vat_result and cn_vat_result[0].vat_amount is not None else 0
	
	# Net Output VAT is Sales VAT minus Credit Note VAT
	return sales_vat - cn_vat

def get_box_2(company, from_date, to_date, output_vat_account):
	"""
	Box 2: VAT due on acquisitions from EU countries (reverse charge)
	This function calculates the VAT due on reverse charge transactions from EU suppliers,
	properly accounting for adjustments via Debit Notes.
	
	Parameters:
	- company (str): Company for which to calculate VAT
	- from_date (str): Start date for the calculation period
	- to_date (str): End date for the calculation period
	- output_vat_account (str): Output VAT account to use for reverse charge calculation
	
	Returns:
	- float: Total reverse charge VAT amount (net of adjustments)
	"""
	# Get company abbreviation to identify reverse charge templates
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	reverse_charge_template = f"Reverse Charge Services - {company_abbr}"
	
	# Query for VAT due on reverse charge purchases (credits to Output VAT)
	rc_query = """
		SELECT SUM(
			CASE 
				WHEN gle.credit > 0 THEN gle.credit
				WHEN gle.debit < 0 THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
		AND pi.taxes_and_charges = %s
		AND pi.is_return = 0
	"""
	
	# Execute query for reverse charge purchases
	rc_result = frappe.db.sql(rc_query, [from_date, to_date, company, output_vat_account, reverse_charge_template], as_dict=1)
	rc_vat = flt(rc_result[0].vat_amount) if rc_result and rc_result[0].vat_amount is not None else 0
	
	# Query for adjustments to reverse charge via Debit Notes (debits to Output VAT)
	rc_debit_note_query = """
		SELECT SUM(
			CASE 
				WHEN gle.debit > 0 THEN gle.debit
				WHEN gle.credit < 0 THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
		AND pi.taxes_and_charges = %s
		AND pi.is_return = 1
	"""
	
	# Execute query for Debit Notes
	rc_dn_result = frappe.db.sql(rc_debit_note_query, [from_date, to_date, company, output_vat_account, reverse_charge_template], as_dict=1)
	rc_dn_vat = flt(rc_dn_result[0].vat_amount) if rc_dn_result and rc_dn_result[0].vat_amount is not None else 0
	
	# Net reverse charge VAT is the standard amount minus any debit note adjustments
	return rc_vat - rc_dn_vat

def get_box_4(company, from_date, to_date, input_vat_account):
	"""
	Box 4: VAT reclaimed on purchases and other inputs
	This function calculates the Input VAT that can be reclaimed from purchases,
	properly accounting for purchase returns and adjustments.
	
	Parameters:
	- company (str): Company for which to calculate VAT
	- from_date (str): Start date for the calculation period
	- to_date (str): End date for the calculation period
	- input_vat_account (str): Input VAT account to use for calculation
	
	Returns:
	- float: Total reclaimable Input VAT amount (net of adjustments)
	"""
	# Query for Input VAT from regular purchases (debits to Input VAT)
	purchase_vat_query = """
		SELECT SUM(
			CASE 
				WHEN gle.debit > 0 THEN gle.debit
				WHEN gle.credit < 0 THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
		AND gle.voucher_no IN (
			SELECT name 
			FROM `tabPurchase Invoice` 
			WHERE is_return = 0
			AND posting_date BETWEEN %s AND %s
			AND company = %s
			AND docstatus = 1
		)
	"""
	
	# Execute query for purchase invoices
	purchase_vat_result = frappe.db.sql(purchase_vat_query, [
		from_date, to_date, company, input_vat_account, from_date, to_date, company
	], as_dict=1)
	purchase_vat = flt(purchase_vat_result[0].vat_amount) if purchase_vat_result and purchase_vat_result[0].vat_amount is not None else 0
	
	# Query for Input VAT adjustments from Debit Notes (credits to Input VAT)
	debit_note_query = """
		SELECT SUM(
			CASE 
				WHEN gle.credit > 0 THEN gle.credit
				WHEN gle.debit < 0 THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
		AND gle.voucher_no IN (
			SELECT name 
			FROM `tabPurchase Invoice` 
			WHERE is_return = 1
			AND posting_date BETWEEN %s AND %s
			AND company = %s
			AND docstatus = 1
		)
	"""
	
	# Execute query for debit notes
	dn_vat_result = frappe.db.sql(debit_note_query, [
		from_date, to_date, company, input_vat_account, from_date, to_date, company
	], as_dict=1)
	dn_vat = flt(dn_vat_result[0].vat_amount) if dn_vat_result and dn_vat_result[0].vat_amount is not None else 0
	
	# Get company abbreviation to identify reverse charge templates
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	reverse_charge_template = f"Reverse Charge Services - {company_abbr}"
	
	# Query for Input VAT from reverse charge transactions (debits to Input VAT)
	rc_input_query = """
		SELECT SUM(
			CASE 
				WHEN gle.debit > 0 THEN gle.debit
				WHEN gle.credit < 0 THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Purchase Invoice'
		AND pi.taxes_and_charges = %s
		AND pi.is_return = 0
	"""
	
	# Execute query for reverse charge purchases (input VAT portion)
	rc_input_result = frappe.db.sql(rc_input_query, [
		from_date, to_date, company, input_vat_account, reverse_charge_template
	], as_dict=1)
	rc_input_vat = flt(rc_input_result[0].vat_amount) if rc_input_result and rc_input_result[0].vat_amount is not None else 0
	
	# Query for Input VAT adjustments from reverse charge Debit Notes (credits to Input VAT)
	rc_input_dn_query = """
		SELECT SUM(
			CASE 
				WHEN gle.credit > 0 THEN gle.credit
				WHEN gle.debit < 0 THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND pi.taxes_and_charges = %s
		AND pi.is_return = 1
	"""
	
	# Execute query for reverse charge debit notes (input VAT portion)
	rc_input_dn_result = frappe.db.sql(rc_input_dn_query, [
		from_date, to_date, company, input_vat_account, reverse_charge_template
	], as_dict=1)
	rc_input_dn_vat = flt(rc_input_dn_result[0].vat_amount) if rc_input_dn_result and rc_input_dn_result[0].vat_amount is not None else 0
	
	# Net Input VAT calculation:
	# Regular Input VAT + Reverse Charge Input VAT - Debit Note adjustments - Reverse Charge Debit Note adjustments
	return purchase_vat + rc_input_vat - dn_vat - rc_input_dn_vat

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
