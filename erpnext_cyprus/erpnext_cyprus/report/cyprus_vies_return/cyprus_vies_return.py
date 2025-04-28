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
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 300,
		},
		{
			"label": _("Billing Country"),
			"fieldname": "country",
			"fieldtype": "Data",
			"width": 150
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
		frappe.msgprint(_("No tax accounts found for company {0}").format(company))
		return []
	
	# Get all output VAT accounts
	output_vat_accounts = [
		tax_accounts["vat"]
	]
	if "oss_vat" in tax_accounts and tax_accounts["oss_vat"]:
		output_vat_accounts.append(tax_accounts["oss_vat"])
	
	# Filter out None values (accounts that might not exist)
	output_vat_accounts = [acc for acc in output_vat_accounts if acc]
	
	# Get EU countries except Cyprus
	eu_countries = get_eu_countries()
	
	# Query to get sales invoices grouped by customer
	customer_totals = frappe.db.sql(
		"""
		SELECT 
			si.customer,
			c.tax_id,
			addr.country,
			SUM(si.net_total) as net_total,
			SUM(ROUND(si.net_total, 0)) as rounded_net_total
		FROM 
			`tabSales Invoice` si
		INNER JOIN 
			`tabCustomer` c ON si.customer = c.name
		LEFT JOIN
			`tabDynamic Link` dl ON dl.link_doctype = 'Customer' AND dl.link_name = si.customer AND dl.parenttype = 'Address'
		LEFT JOIN
			`tabAddress` addr ON addr.name = dl.parent AND addr.is_primary_address = 1
		WHERE 
			si.docstatus = 1
			AND si.company = %s
			AND si.posting_date BETWEEN %s AND %s
			AND c.customer_group = 'Commercial'
			AND c.tax_id IS NOT NULL AND c.tax_id != ''
			AND addr.country IN %s
		GROUP BY
			si.customer, c.tax_id, addr.country
		ORDER BY 
			addr.country, si.customer
		""",
		(company, from_date, to_date, tuple(eu_countries)),
		as_dict=1,
	)
	
	return customer_totals

