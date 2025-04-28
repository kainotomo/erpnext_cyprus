# Copyright (c) 2025, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.utils.tax_utils import get_tax_accounts
from erpnext_cyprus.utils.tax_utils import get_eu_countries

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	columns = [
		{
			"label": _("Sales Invoice"),
			"fieldtype": "Link",
			"fieldname": "name",
			"options": "Sales Invoice",
			"width": 200,
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 300,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Tax ID"),
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Rounded Net Total"),
			"fieldname": "rounded_net_total",
			"fieldtype": "Currency",
			"width": 100
		},
	]
	 
	return columns


def get_data(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	
	if not company or not from_date or not to_date:
		return []
	
	# Get VAT tax accounts for the company
	tax_accounts = get_tax_accounts(company)
	if not tax_accounts:
		return 0
	
	# Get all output VAT accounts
	output_vat_accounts = [
		tax_accounts["oss_vat"]
	]
	
	# Filter out None values (accounts that might not exist)
	output_vat_accounts = [acc for acc in output_vat_accounts if acc]
	
	# Query to get sales invoices meeting the criteria
	sales_invoices = frappe.db.sql(
		"""
		SELECT 
			si.name,
			si.customer,
			si.posting_date,
			c.tax_id,
			si.net_total,
			ROUND(si.net_total, 0) as rounded_net_total
		FROM 
			`tabSales Invoice` si
		INNER JOIN 
			`tabCustomer` c ON si.customer = c.name
		WHERE 
			si.docstatus = 1
			AND si.company = %s
			AND si.posting_date BETWEEN %s AND %s
			AND c.customer_group = 'Commercial'
			AND c.tax_id IS NOT NULL AND c.tax_id != ''
			AND NOT EXISTS (
				SELECT 1 
				FROM `tabSales Taxes and Charges` stc
				WHERE 
					stc.parent = si.name 
					AND stc.account_head IN %s
			)
		ORDER BY 
			si.posting_date
		""",
		(company, from_date, to_date, tuple(output_vat_accounts) if output_vat_accounts else ('',)),
		as_dict=1,
	)
	
	return sales_invoices

