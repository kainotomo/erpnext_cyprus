# Copyright (c) 2025, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _

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
			"label": _("Amount"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Rounded Amount"),
			"fieldname": "rounded_grand_total",
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