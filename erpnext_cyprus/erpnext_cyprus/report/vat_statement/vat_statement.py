# Copyright (c) 2024, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_filters(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	cost_center = filters.get("cost_center")
	cyprus_vat_output_account = filters.get("cyprus_vat_output_account")
	cyprus_vat_input_account = filters.get("cyprus_vat_input_account")
	return company, from_date, to_date, cost_center, cyprus_vat_output_account, cyprus_vat_input_account

def get_columns():
	columns = [
		{
			"label": _("Description"),
			"fieldtype": "Data",
			"fieldname": "description",
			"width": 800,
		},
		{
			"label": _("#"),
			"fieldtype": "Data",
			"fieldname": "desc_id",
			"width": 50,
		},
		{
			"label": _("Amount"),
			"fieldtype": "Currency",
			"fieldname": "amount",
			"options": "currency",
			"width": 100,
		}
	]
	 
	return columns

def get_vat_due_on_sales(company, from_date, to_date, cost_center, cyprus_vat_output_account):
	"""
	Calculate the total VAT due on sales for the VAT return period.
	
	This function queries the GL Entries table to find all VAT collected on sales transactions.
	It handles both regular sales (which appear as credit entries in the VAT account) and
	return sales (which appear as debit entries in the VAT account).
	
	The function:
	1. Filters GL entries by company, date range, and the specified VAT output account
	2. Separates regular sales (credit entries) and return sales (debit entries)
	3. Returns the net VAT amount (regular sales VAT minus return sales VAT)
	
	Parameters:
	- company (str): The company for which to calculate VAT
	- from_date (date): Start date of the VAT period
	- to_date (date): End date of the VAT period
	- cost_center (str, optional): Cost center to filter transactions
	- cyprus_vat_output_account (str): The VAT output account used for collecting sales tax
	
	Returns:
	- float: The net VAT amount due on sales for the period
	"""
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"account = %s"
	]
	values = [company, from_date, to_date, cyprus_vat_output_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	# Separate credit and debit for regular and return invoices
	query = """
		SELECT 
			SUM(CASE WHEN voucher_type = 'Sales Invoice' AND credit > 0 THEN credit ELSE 0 END) as regular_credit,
			SUM(CASE WHEN voucher_type = 'Sales Invoice' AND debit > 0 THEN debit ELSE 0 END) as return_debit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	regular_credit = result[0].get('regular_credit') if result and result[0].get('regular_credit') is not None else 0
	return_debit = result[0].get('return_debit') if result and result[0].get('return_debit') is not None else 0
	
	# Return VAT appears as debit entries, so subtract from regular credits
	total_vat_due = regular_credit - return_debit
	
	return total_vat_due

def get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account):
	"""
	Calculate the total VAT due on acquisitions from EU member states.
	
	This function queries the GL Entries table to find VAT that is due on purchases
	from other EU countries. In reverse charge scenarios, the VAT that would normally
	be paid to suppliers is instead accounted for in the output tax account.
	
	The function:
	1. Filters GL entries by company, date range, and the specified VAT output account
	2. Only includes credit entries from Purchase Invoices (reverse charge entries)
	3. Returns the total credit amount which represents VAT due on EU acquisitions
	
	Parameters:
	- company (str): The company for which to calculate VAT
	- from_date (date): Start date of the VAT period
	- to_date (date): End date of the VAT period
	- cost_center (str, optional): Cost center to filter transactions
	- cyprus_vat_output_account (str): The VAT output account used for reverse charge
	
	Returns:
	- float: The total VAT amount due on EU acquisitions for the period
	"""
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"credit > 0",
		"account = %s",
		"voucher_type = 'Purchase Invoice'"
	]
	values = [company, from_date, to_date, cyprus_vat_output_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(credit) as total_credit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_credit = result[0].get('total_credit') if result and result[0].get('total_credit') is not None else 0
	return total_credit

def get_vat_reclaimed_on_purchases(company, from_date, to_date, cost_center, cyprus_vat_input_account):
	"""
	Calculate the total VAT reclaimed on purchases for the VAT return period.
	
	This function queries the GL Entries table to find all VAT paid on purchase transactions
	that is eligible to be reclaimed as input tax. It looks at debit entries in the
	specified VAT input account.
	
	The function:
	1. Filters GL entries by company, date range, and the specified VAT input account
	2. Only includes debit entries (which represent VAT paid that can be reclaimed)
	3. Returns the total debit amount which represents reclaimable VAT
	
	Parameters:
	- company (str): The company for which to calculate VAT
	- from_date (date): Start date of the VAT period
	- to_date (date): End date of the VAT period
	- cost_center (str, optional): Cost center to filter transactions
	- cyprus_vat_input_account (str): The VAT input account used for recording reclaimable VAT
	
	Returns:
	- float: The total VAT amount reclaimable on purchases for the period
	"""
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"debit > 0",
		"account = %s"
	]
	values = [company, from_date, to_date, cyprus_vat_input_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(debit) as total_debit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_debit = result[0].get('total_debit') if result and result[0].get('total_debit') is not None else 0
	return total_debit

def get_total_value_of_sales_excluding_vat(company, from_date, to_date, cost_center):
	"""
	Calculate the total value of sales excluding VAT for the VAT return period.
	
	This function queries the Sales Invoice table to get the net total (excluding VAT)
	of all sales transactions within the period. It handles both regular sales invoices
	and return invoices separately to ensure accurate calculation.
	
	The function:
	1. Filters Sales Invoices by company, date range, and valid document status
	2. Separates regular sales and return sales for proper accounting
	3. Returns the total net amount of all sales excluding VAT
	
	Note: Return invoices already have negative base_net_total values, so they are
	added to get the correct net effect.
	
	Parameters:
	- company (str): The company for which to calculate sales
	- from_date (date): Start date of the VAT period
	- to_date (date): End date of the VAT period
	- cost_center (str, optional): Cost center to filter transactions
	
	Returns:
	- float: The total value of sales excluding VAT for the period
	"""
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	# Query for regular invoices
	query = """
		SELECT 
			SUM(CASE WHEN is_return = 0 THEN base_net_total ELSE 0 END) as invoice_amount,
			SUM(CASE WHEN is_return = 1 THEN base_net_total ELSE 0 END) as return_amount
		FROM `tabSales Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	invoice_amount = result[0].get('invoice_amount') if result and result[0].get('invoice_amount') is not None else 0
	return_amount = result[0].get('return_amount') if result and result[0].get('return_amount') is not None else 0
	
	# Return invoices already have negative base_net_total, so we add to get the net effect
	total_net_amount = invoice_amount + return_amount
	
	return total_net_amount

def get_total_value_of_purchases_excluding_vat(company, from_date, to_date, cost_center):
	"""
	Calculate the total value of purchases excluding VAT for the VAT return period.
	
	This function queries the Purchase Invoice table to get the net total (excluding VAT)
	of all purchase transactions within the period. It handles both regular purchase invoices
	and return invoices separately to ensure accurate calculation.
	
	The function:
	1. Filters Purchase Invoices by company, date range, and valid document status
	2. Separates regular purchases and return purchases for proper accounting
	3. Returns the total net amount of all purchases excluding VAT
	
	Note: Return invoices already have negative base_net_total values, so they are
	added to get the correct net effect.
	
	Parameters:
	- company (str): The company for which to calculate purchases
	- from_date (date): Start date of the VAT period
	- to_date (date): End date of the VAT period
	- cost_center (str, optional): Cost center to filter transactions
	
	Returns:
	- float: The total value of purchases excluding VAT for the period
	"""
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT 
			SUM(CASE WHEN is_return = 0 THEN base_net_total ELSE 0 END) as invoice_amount,
			SUM(CASE WHEN is_return = 1 THEN base_net_total ELSE 0 END) as return_amount
		FROM `tabPurchase Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	invoice_amount = result[0].get('invoice_amount') if result and result[0].get('invoice_amount') is not None else 0
	return_amount = result[0].get('return_amount') if result and result[0].get('return_amount') is not None else 0
	
	# Return invoices already have negative base_net_total, so we add to get the net effect
	total_net_amount = invoice_amount + return_amount
	
	return total_net_amount

def get_total_value_of_goods_supplied_to_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account):
    """
    Calculate the total value of goods supplied to EU member states (Box 8A).
    
    This function queries Sales Invoices to find sales of goods (not services) made to
    customers in other EU countries. It identifies these transactions by looking for any of:
    1. Customers with tax_id starting with EU country codes (except Cyprus), with zero tax or empty tax, OR
    2. Sales that use a special VAT account different from the standard Cyprus VAT output account, OR
    3. Customers with no tax_id and zero tax or empty tax
    
    The function:
    1. Filters Sales Invoices by company, date range, and valid document status
    2. Identifies EU transactions using the conditions mentioned above
    3. Identifies items that are goods (not services) by checking custom_is_service flag
    4. Sums the net amount of all goods sold to EU customers
    
    Parameters:
    - company (str): The company for which to calculate EU goods exports
    - from_date (date): Start date of the VAT period
    - to_date (date): End date of the VAT period
    - cost_center (str, optional): Cost center to filter transactions
    - cyprus_vat_output_account (str): The standard VAT output account to exclude
    
    Returns:
    - float: The total value of goods supplied to EU member states excluding VAT
    """
    # Build list of tax_id prefixes to match (EU country codes except Cyprus)
    tax_id_inclusions = []
    for country_code in vies_countries:
        if country_code != "CY":  # Exclude Cyprus
            tax_id_inclusions.append(f"LEFT(c.tax_id, 2) = '{country_code}'")
    
    # Join the inclusions with OR since we want to match any EU country code
    eu_tax_id_condition = " OR ".join(tax_id_inclusions)
    
    conditions = [
        "si.company = %s",
        "si.posting_date >= %s",
        "si.posting_date <= %s",
        "si.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
        "si.docstatus = 1",
        # Any of these conditions:
        # 1. Customer has tax_id starting with EU country code (except Cyprus) with zero/empty tax, OR
        # 2. VAT account used is not cyprus_vat_output_account, OR
        # 3. Customer has no tax_id and zero/empty tax
        f"((c.tax_id IS NOT NULL AND c.tax_id != '' AND ({eu_tax_id_condition}) AND (si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)) OR EXISTS (SELECT 1 FROM `tabSales Taxes and Charges` stc WHERE stc.parent = si.name AND stc.account_head != %s) OR (c.tax_id IS NULL AND (si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)))"
    ]
    values = [company, from_date, to_date, cyprus_vat_output_account]

    if cost_center:
        conditions.append("si.cost_center = %s")
        values.append(cost_center)

    query = """
        SELECT 
            si.name as invoice_name,
            si.is_return,
            SUM(CASE 
                WHEN i.custom_is_service = 0 OR i.custom_is_service IS NULL 
                THEN sii.base_net_amount 
                ELSE 0 
            END) as goods_amount
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON si.customer = c.name
        LEFT JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        LEFT JOIN `tabItem` i ON sii.item_code = i.name
        WHERE {conditions}
        GROUP BY si.name, si.is_return
    """.format(conditions=" AND ".join(conditions))

    result = frappe.db.sql(query, values, as_dict=True)
    
    # Sum up all goods amounts, properly handling returns
    total_goods_amount = 0
    for row in result:
        amount = row.get('goods_amount') if row.get('goods_amount') is not None else 0
        # Adjust amounts for returns - if it's a return and the amount is positive, make it negative
        if row.get('is_return') and amount > 0:
            amount = -amount
        total_goods_amount += amount
    
    return total_goods_amount

def get_total_value_of_services_supplied_to_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account):
    """
    Calculate the total value of services supplied to EU member states (Box 8B).
    
    This function queries Sales Invoices to find sales of services (not goods) made to
    customers in other EU countries. It identifies these transactions by looking for any of:
    1. Customers with tax_id starting with EU country codes (except Cyprus), with zero tax or empty tax, OR
    2. Sales that use a special VAT account different from the standard Cyprus VAT output account, OR
    3. Customers with no tax_id and zero tax or empty tax
    
    The function:
    1. Filters Sales Invoices by company, date range, and valid document status
    2. Identifies EU transactions using the conditions mentioned above
    3. Identifies items that are services (not goods) by checking custom_is_service flag
    4. Sums the net amount of all services sold to EU customers
    
    Parameters:
    - company (str): The company for which to calculate EU services exports
    - from_date (date): Start date of the VAT period
    - to_date (date): End date of the VAT period
    - cost_center (str, optional): Cost center to filter transactions
    - cyprus_vat_output_account (str): The standard VAT output account to exclude
    
    Returns:
    - float: The total value of services supplied to EU member states excluding VAT
    """
    # Build list of tax_id prefixes to match (EU country codes except Cyprus)
    tax_id_inclusions = []
    for country_code in vies_countries:
        if country_code != "CY":  # Exclude Cyprus
            tax_id_inclusions.append(f"LEFT(c.tax_id, 2) = '{country_code}'")
    
    # Join the inclusions with OR since we want to match any EU country code
    eu_tax_id_condition = " OR ".join(tax_id_inclusions)
    
    conditions = [
        "si.company = %s",
        "si.posting_date >= %s",
        "si.posting_date <= %s",
        "si.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
        "si.docstatus = 1",
        # Any of these conditions:
        # 1. Customer has tax_id starting with EU country code (except Cyprus) with zero/empty tax, OR
        # 2. VAT account used is not cyprus_vat_output_account, OR
        # 3. Customer has no tax_id and zero/empty tax
        f"((c.tax_id IS NOT NULL AND c.tax_id != '' AND ({eu_tax_id_condition}) AND (si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)) OR EXISTS (SELECT 1 FROM `tabSales Taxes and Charges` stc WHERE stc.parent = si.name AND stc.account_head != %s) OR (c.tax_id IS NULL AND (si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)))"
    ]
    values = [company, from_date, to_date, cyprus_vat_output_account]

    if cost_center:
        conditions.append("si.cost_center = %s")
        values.append(cost_center)

    query = """
        SELECT 
            si.name as invoice_name,
            si.is_return,
            SUM(CASE 
                WHEN i.custom_is_service = 1 
                THEN sii.base_net_amount 
                ELSE 0 
            END) as services_amount
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON si.customer = c.name
        LEFT JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        LEFT JOIN `tabItem` i ON sii.item_code = i.name
        WHERE {conditions}
        GROUP BY si.name, si.is_return
    """.format(conditions=" AND ".join(conditions))

    result = frappe.db.sql(query, values, as_dict=True)
    
    # Sum up all services amounts, properly handling returns
    total_services_amount = 0
    for row in result:
        amount = row.get('services_amount') if row.get('services_amount') is not None else 0
        # Adjust amounts for returns - if it's a return and the amount is positive, make it negative
        if row.get('is_return') and amount > 0:
            amount = -amount
        total_services_amount += amount
    
    return total_services_amount

def get_total_value_of_zero_rated_supplies(company, from_date, to_date, cost_center, vies_countries):
    """
    Calculate the total value of zero-rated supplies (Box 9).
    
    This function identifies zero-rated supplies that are made to non-EU countries.
    It looks for sales transactions that meet these criteria:
    1. Invoices have zero tax or no tax applied
    2. Customer has a tax_id that doesn't start with any EU country code
    
    The function:
    1. Filters Sales Invoices by company, date range, and valid document status
    2. Checks that no VAT was charged (zero-rated)
    3. Ensures the customer has a tax_id not from EU countries (typically exports outside EU)
    4. Sums all matching sales, properly handling returns
    
    Parameters:
    - company (str): The company for which to calculate zero-rated supplies
    - from_date (date): Start date of the VAT period
    - to_date (date): End date of the VAT period
    - cost_center (str, optional): Cost center to filter transactions
    - vies_countries (list): List of EU country codes to exclude
    
    Returns:
    - float: The total value of zero-rated supplies excluding VAT
    """
    # Build a list of tax_id prefixes to exclude (EU country codes)
    tax_id_conditions = []
    for country_code in vies_countries:
        tax_id_conditions.append(f"LEFT(c.tax_id, 2) != '{country_code}'")
    
    # Join the exclusions with AND to make sure all are satisfied
    tax_id_condition = " AND ".join(tax_id_conditions)
    
    conditions = [
        "si.company = %s",
        "si.posting_date >= %s",
        "si.posting_date <= %s",
        "si.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
        "si.docstatus = 1",
        # Zero or no tax
        "(si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)",
        # Customer has tax_id
        "c.tax_id IS NOT NULL AND c.tax_id != ''",
        # Tax ID first two characters aren't in VIES countries
        f"({tax_id_condition})"
    ]
    values = [company, from_date, to_date]

    if cost_center:
        conditions.append("si.cost_center = %s")
        values.append(cost_center)

    query = """
        SELECT 
            si.name as invoice_name,
            si.is_return,
            si.base_net_total as net_amount
        FROM `tabSales Invoice` si
        JOIN `tabCustomer` c ON si.customer = c.name
        WHERE {conditions}
    """.format(conditions=" AND ".join(conditions))

    result = frappe.db.sql(query, values, as_dict=True)
    
    # Sum up all zero-rated amounts, handling returns properly
    total_zero_rated_amount = 0
    for row in result:
        amount = row.get('net_amount') if row.get('net_amount') is not None else 0
        # Adjust amounts for returns
        if row.get('is_return') and amount > 0:
            amount = -amount
        total_zero_rated_amount += amount
    
    return total_zero_rated_amount

def get_total_value_of_out_of_scope_sales(company, from_date, to_date, cost_center):
	conditions = [
		"si.company = %s",
		"si.posting_date >= %s",
		"si.posting_date <= %s",
		"si.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"si.docstatus = 1",
		# Zero tax (out of scope)
		"(si.total_taxes_and_charges = 0 OR si.taxes_and_charges IS NULL)",
		# Not already counted in other boxes
		"NOT EXISTS (SELECT 1 FROM `tabCustomer` c WHERE c.name = si.customer AND c.tax_id IS NOT NULL AND c.tax_id != '')"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("si.cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT 
			si.name,
			si.is_return,
			si.base_net_total
		FROM `tabSales Invoice` si
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	# Sum with proper return handling
	total_out_of_scope = 0
	for row in result:
		amount = row.get('base_net_total') if row.get('base_net_total') is not None else 0
		if row.get('is_return') and amount > 0:
			amount = -amount
		total_out_of_scope += amount
	
	return total_out_of_scope

def get_total_value_of_acquisitions_from_eu(company, from_date, to_date, cost_center, vies_countries):
	"""
	Calculate total value of acquisitions of goods from other EU member states (Box 11A)
	This includes purchases with tax_id starting with EU country codes (except Cyprus)
	and where the items are goods (not services)
	"""
	# Build list of tax_id prefixes to match (EU country codes except Cyprus)
	tax_id_inclusions = []
	for country_code in vies_countries:
		if country_code != "CY":  # Exclude Cyprus
			tax_id_inclusions.append(f"LEFT(pi.tax_id, 2) = '{country_code}'")
	
	# Join the inclusions with OR since we want to match any EU country code
	tax_id_condition = " OR ".join(tax_id_inclusions)
	
	conditions = [
		"pi.company = %s",
		"pi.posting_date >= %s",
		"pi.posting_date <= %s",
		"pi.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"pi.docstatus = 1",
		# Supplier must have tax_id starting with EU country code (except Cyprus)
		"pi.tax_id IS NOT NULL AND pi.tax_id != ''",
		f"({tax_id_condition})"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("pi.cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT 
			pi.name as invoice_name,
			pi.is_return,
			SUM(CASE 
				WHEN i.custom_is_service = 0 OR i.custom_is_service IS NULL 
				THEN pii.base_net_amount 
				ELSE 0 
			END) as goods_amount
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabItem` i ON pii.item_code = i.name
		WHERE {conditions}
		GROUP BY pi.name, pi.is_return
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	# Sum up all goods amounts, handling returns properly
	total_goods_amount = 0
	for row in result:
		amount = row.get('goods_amount') if row.get('goods_amount') is not None else 0
		# Adjust amounts for returns - if it's a return and the amount is positive, make it negative
		if row.get('is_return') and amount > 0:
			amount = -amount
		total_goods_amount += amount
	
	return total_goods_amount

def get_total_value_of_services_received_excluding_vat(company, from_date, to_date, cost_center, vies_countries):
	"""
	Calculate total value of services received from abroad (Box 11B)
	This includes purchases with tax_id starting with any country code
	and where the items are services (custom_is_service = 1)
	"""
	# Build list of tax_id prefixes to match (any country code)
	conditions = [
		"pi.company = %s",
		"pi.posting_date >= %s",
		"pi.posting_date <= %s",
		"pi.status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"pi.docstatus = 1",
		# Supplier must have tax_id 
		"pi.tax_id IS NOT NULL AND pi.tax_id != ''"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("pi.cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT 
			pi.name as invoice_name,
			pi.is_return,
			SUM(CASE 
				WHEN i.custom_is_service = 1
				THEN pii.base_net_amount 
				ELSE 0 
			END) as services_amount
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabItem` i ON pii.item_code = i.name
		WHERE {conditions}
		GROUP BY pi.name, pi.is_return
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	
	# Sum up all services amounts, handling returns properly
	total_services_amount = 0
	for row in result:
		amount = row.get('services_amount') if row.get('services_amount') is not None else 0
		# Adjust amounts for returns - if it's a return and the amount is positive, make it negative
		if row.get('is_return') and amount > 0:
			amount = -amount
		total_services_amount += amount
	
	return total_services_amount

vies_countries = [
	"AT",  # Austria
	"BE",  # Belgium
	"BG",  # Bulgaria
	"HR",  # Croatia
	"CY",  # Cyprus
	"CZ",  # Czech Republic
	"DK",  # Denmark
	"EE",  # Estonia
	"FI",  # Finland
	"FR",  # France
	"DE",  # Germany
	"GR",  # Greece
	"HU",  # Hungary
	"IE",  # Ireland
	"IT",  # Italy
	"LV",  # Latvia
	"LT",  # Lithuania
	"LU",  # Luxembourg
	"MT",  # Malta
	"NL",  # Netherlands
	"PL",  # Poland
	"PT",  # Portugal
	"RO",  # Romania
	"SK",  # Slovakia
	"SI",  # Slovenia
	"ES",  # Spain
	"SE",  # Sweden
]

def execute(filters=None):
	columns = get_columns()
	company, from_date, to_date, cost_center, cyprus_vat_output_account, cyprus_vat_input_account = get_filters(filters)
	data = []
	
	vat_due_on_sales = get_vat_due_on_sales(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on sales and other outputs", "desc_id": "1", "amount": vat_due_on_sales}
	data.append(row)
	
	vat_due_on_acquisitions_eu = get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on the acquisitions from other EU Members States", "desc_id": "2", "amount": vat_due_on_acquisitions_eu}
	data.append(row)

	total_vat_due = vat_due_on_sales + vat_due_on_acquisitions_eu
	row = {"description": "Total VAT due", "desc_id": "3", "amount": total_vat_due}
	data.append(row)

	vat_reclaimed_on_purchases = get_vat_reclaimed_on_purchases(company, from_date, to_date, cost_center, cyprus_vat_input_account)
	row = {"description": "VAT reclaimed in the period for purchases and other inputs (including acquisitions from EU)", "desc_id": "4", "amount": vat_reclaimed_on_purchases}
	data.append(row)

	net_vat_to_be_paid_or_reclaimed = total_vat_due - vat_reclaimed_on_purchases
	row = {"description": "Net VAT to be paid or reclaimed", "desc_id": "5", "amount": net_vat_to_be_paid_or_reclaimed}
	data.append(row)

	total_value_of_sales_excluding_vat = get_total_value_of_sales_excluding_vat(company, from_date, to_date, cost_center)
	row = {"description": "Total value of sales and other outputs excluding any VAT (including the amounts in boxes 8A, 8B, 9, 10 and 11B)", "desc_id": "6", "amount": total_value_of_sales_excluding_vat}
	data.append(row)

	total_value_of_purchases_excluding_vat = get_total_value_of_purchases_excluding_vat(company, from_date, to_date, cost_center)
	row = {"description": "Total value of purchases and other inputs excluding any VAT (including the amounts in box 11A and 11B)", "desc_id": "7", "amount": total_value_of_purchases_excluding_vat}
	data.append(row)

	total_value_of_supply_of_goods_and_services_to_eu = get_total_value_of_goods_supplied_to_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "Total value of supply of goods and related services (excluding VAT) to other Member States", "desc_id": "8A", "amount": total_value_of_supply_of_goods_and_services_to_eu}
	data.append(row)

	total_value_of_services_supplied_to_eu = get_total_value_of_services_supplied_to_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "Total value of services supplied (excluding VAT) to other Member States", "desc_id": "8B", "amount": total_value_of_services_supplied_to_eu}
	data.append(row)

	total_value_of_zero_rated_supplies = get_total_value_of_zero_rated_supplies(company, from_date, to_date, cost_center, vies_countries)
	row = {"description": "Total value of outputs on zero-rated supplies (other than those included in box 8A)", "desc_id": "9", "amount": total_value_of_zero_rated_supplies}
	data.append(row)

	total_value_of_out_of_scope_sales = get_total_value_of_out_of_scope_sales(company, from_date, to_date, cost_center)
	row = {"description": "Total value of out of scope sales, with right of deduction of input tax (other than those included in box 8B)", "desc_id": "10", "amount": total_value_of_out_of_scope_sales}
	data.append(row)

	total_value_of_acquisitions_from_eu = get_total_value_of_acquisitions_from_eu(company, from_date, to_date, cost_center, vies_countries)
	row = {"description": "Total value of all acquisitions of goods and related services (excluding any VAT) from other EU member States", "desc_id": "11A", "amount": total_value_of_acquisitions_from_eu}
	data.append(row)

	total_value_of_services_received_excluding_vat = get_total_value_of_services_received_excluding_vat(company, from_date, to_date, cost_center, vies_countries)
	row = {"description": "Total value of all services received (excluding any VAT)", "desc_id": "11B", "amount": total_value_of_services_received_excluding_vat}
	data.append(row)

	return columns, data
