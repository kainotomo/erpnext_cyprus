# Copyright (c) 2025, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.utils.tax_utils import get_eu_countries

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	columns = [
		{
			"label": _("Country"),
			"fieldname": "country",
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
			"label": _("Total Taxes"),
			"fieldname": "total_taxes_and_charges",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Tax Rate (%)"),
			"fieldname": "tax_rate",
			"fieldtype": "Percent",
			"width": 100
		},
		{
			"label": _("Grand Total"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 100
		}
	]
	 
	return columns

def get_data(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	
	if not company or not from_date or not to_date:
		return []
	
	# Get EU countries except Cyprus
	eu_countries = get_eu_countries()
	
	# Fetch and group data in a single query
	results = frappe.db.sql(
		"""
		SELECT 
			addr.country,
			SUM(si.net_total) as net_total,
			SUM(si.total_taxes_and_charges) as total_taxes_and_charges,
			ROUND((SUM(si.total_taxes_and_charges) / SUM(si.net_total) * 100), 0) as tax_rate,
			SUM(si.grand_total) as grand_total
		FROM 
			`tabSales Invoice` si
		INNER JOIN 
			`tabCustomer` c ON si.customer = c.name
		LEFT JOIN
			`tabDynamic Link` dl ON dl.link_doctype = 'Customer' AND dl.link_name = si.customer AND dl.parenttype = 'Address'
		LEFT JOIN
			`tabAddress` addr ON addr.name = dl.parent
		WHERE 
			si.docstatus = 1
			AND si.company = %s
			AND si.posting_date BETWEEN %s AND %s
			AND si.total_taxes_and_charges != 0
			AND addr.country IN %s
		GROUP BY
			addr.country
		ORDER BY 
			addr.country
		""",
		(company, from_date, to_date, tuple(eu_countries)),
		as_dict=1,
	)
	
	return results

