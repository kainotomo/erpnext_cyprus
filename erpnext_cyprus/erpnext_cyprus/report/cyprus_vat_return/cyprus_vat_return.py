# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_first_day, get_last_day, add_days, add_months
from erpnext_cyprus.utils.tax_utils import get_tax_accounts
from erpnext_cyprus.utils.tax_utils import get_eu_countries

def execute(filters=None):
    # Ensure from_date and to_date are set
    if not filters.get('from_date') or not filters.get('to_date'):
        fiscal_year = filters.get('fiscal_year')
        quarter = filters.get('quarter')
        if fiscal_year and quarter:
            dates = get_quarter_dates(fiscal_year, quarter)
            filters['from_date'] = dates['from_date']
            filters['to_date'] = dates['to_date']
    
    return get_columns(), get_data(filters)

def get_quarter_dates(fiscal_year, quarter):
    """Get the start and end dates for the specified quarter"""
    if not fiscal_year or not quarter:
        return {'from_date': None, 'to_date': None}
    
    # Get fiscal year start date
    year_details = frappe.get_doc("Fiscal Year", fiscal_year)
    year = getdate(year_details.year_start_date).year
    
    # Extract quarter info
    quarter_start = None
    quarter_end = None
    
    if "Q1" in quarter:
        quarter_start = f"{year}-01-01"
        quarter_end = f"{year}-03-31"
    elif "Q2" in quarter:
        quarter_start = f"{year}-04-01"
        quarter_end = f"{year}-06-30"
    elif "Q3" in quarter:
        quarter_start = f"{year}-07-01"
        quarter_end = f"{year}-09-30"
    elif "Q4" in quarter:
        quarter_start = f"{year}-10-01"
        quarter_end = f"{year}-12-31"
    
    return {
        'from_date': quarter_start,
        'to_date': quarter_end
    }

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
            "width": 300
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
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    
    if not company or not from_date or not to_date:
        return []
    
    # Initialize VAT return data
    vat_return_data = []
    
    # Add VAT Return fields according to Cyprus tax requirements
    # Box 1: VAT due on sales and other outputs
    output_vat = get_box_1(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 1"),
        "description": _("VAT due on sales and other outputs"),
        "amount": output_vat
    })

    # Box 2: VAT due on acquisitions from EU countries
    eu_acquisitions_vat = get_box_2(company, from_date, to_date)
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
    input_vat = get_box_4(company, from_date, to_date)
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
    non_eu_exports = get_non_eu_exports(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 9"),
        "description": _("Total value of exports to non-EU countries"),
        "amount": non_eu_exports
    })
    
    # Box 10: Total value of out-of-scope sales
    out_of_scope = get_out_of_scope_sales(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 10"),
        "description": _("Total value of out-of-scope sales"),
        "amount": out_of_scope
    })
    
    # Box 11A & 11B: EU goods and services acquisitions
    eu_acquisitions_goods = get_eu_goods_acquisitions(company, from_date, to_date)
    eu_acquisitions_services = get_eu_services_acquisitions(company, from_date, to_date)
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

def get_box_1(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get all output VAT accounts
    output_vat_accounts = [
        tax_accounts["vat"]
    ]
    
    # Filter out None values (accounts that might not exist)
    output_vat_accounts = [acc for acc in output_vat_accounts if acc]
    
    if not output_vat_accounts:
        return 0
    
    # Format for SQL IN clause - converting to a proper list of parameters
    placeholder_list = ', '.join(['%s'] * len(output_vat_accounts))
    
    # Query for VAT due on acquisitions, handling Debit Notes differently
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
    params = [from_date, to_date, company] + output_vat_accounts
    
    # Execute query
    output_vat_result = frappe.db.sql(query, params, as_dict=1)
    output_vat = flt(output_vat_result[0].vat_amount) if output_vat_result and output_vat_result[0].vat_amount is not None else 0
    
    return output_vat

def get_box_2(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get all output VAT accounts
    output_vat_accounts = [
        tax_accounts["vat"]
    ]
    
    # Filter out None values (accounts that might not exist)
    output_vat_accounts = [acc for acc in output_vat_accounts if acc]
    
    if not output_vat_accounts:
        return 0
    
    # Format for SQL IN clause - converting to a proper list of parameters
    placeholder_list = ', '.join(['%s'] * len(output_vat_accounts))
    
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
    params = [from_date, to_date, company] + output_vat_accounts
    
    # Execute query
    output_vat_result = frappe.db.sql(query, params, as_dict=1)
    output_vat = flt(output_vat_result[0].vat_amount) if output_vat_result and output_vat_result[0].vat_amount is not None else 0
    
    return output_vat

def get_box_4(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get VAT account
    vat_accounts = [
        tax_accounts["vat"]
    ]
    
    # Filter out None values
    vat_accounts = [acc for acc in vat_accounts if acc]
    
    if not vat_accounts:
        return 0
    
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
    
    # Get service item groups to exclude
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabAddress` addr ON si.customer_address = addr.name
        INNER JOIN `tabCustomer` cust ON si.customer = cust.name
        INNER JOIN `tabItem` item ON sii.item_code = item.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND addr.country IN ({0})
        AND addr.country != 'Cyprus'
        AND cust.customer_type = 'Company'
        AND item.item_group NOT IN ({1})
    """.format(placeholder_list, service_placeholders)
    
    # Build parameters list - add EU countries and service groups to the parameters
    params = [from_date, to_date, company] + eu_countries + (service_groups if service_groups else [])
    
    eu_goods = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_box_8b(company, from_date, to_date):
    # Get EU countries list using utility function
    eu_countries = get_eu_countries()
    
    # Get service item groups
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabAddress` addr ON si.customer_address = addr.name
        INNER JOIN `tabCustomer` cust ON si.customer = cust.name
        INNER JOIN `tabItem` item ON sii.item_code = item.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND addr.country IN ({0})
        AND addr.country != 'Cyprus'
        AND cust.customer_type = 'Company'
        AND item.item_group IN ({1})
    """.format(placeholder_list, service_placeholders)
    
    # Build parameters list
    params = [from_date, to_date, company] + eu_countries + (service_groups if service_groups else [])
    
    eu_services = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_non_eu_exports(company, from_date, to_date):
    # Get EU countries list for exclusion
    eu_countries = get_eu_countries()
    eu_countries.append("Cyprus")
    
    # Get service item groups to exclude
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Get company abbreviation to match template names
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    query = """
        SELECT SUM(
            CASE WHEN si.is_return = 0 THEN si.base_net_total ELSE -si.base_net_total END
        ) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabAddress` addr ON si.customer_address = addr.name
        INNER JOIN `tabItem` item ON sii.item_code = item.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND addr.country NOT IN ({0})
        AND item.item_group NOT IN ({1})
        AND (si.taxes_and_charges = %s OR si.taxes_and_charges IS NULL)
    """.format(placeholder_list, service_placeholders)
    
    # Parameters including the non-EU export template name
    params = [from_date, to_date, company] + eu_countries + (service_groups if service_groups else []) + [f"Non-EU Export - {company_abbr}"]
    
    exports = frappe.db.sql(query, params, as_dict=1)
    
    return flt(exports[0].amount) if exports and exports[0].amount is not None else 0

def get_out_of_scope_sales(company, from_date, to_date):
    # Get company abbreviation to match template names
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    # Get EU countries for exclusion
    eu_countries = get_eu_countries()
    eu_countries.append("Cyprus")  # Add Cyprus to exclusion list
    
    # Out of scope templates
    exempt_templates = [
        f"Exempt Supply - {company_abbr}",
        f"Zero Rated - {company_abbr}"
    ]
    
    # Format for SQL IN clause
    template_placeholders = ', '.join(['%s'] * len(exempt_templates))
    eu_placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    query = """
        SELECT SUM(
            CASE WHEN si.is_return = 0 THEN si.base_net_total ELSE -si.base_net_total END
        ) as amount
        FROM `tabSales Invoice` si
        LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND si.taxes_and_charges IN ({0})
        AND (
            /* Not to EU countries (exclude box 8) */
            addr.country NOT IN ({1})
            /* Not products to non-EU (exclude box 9) */
            OR si.name NOT IN (
                SELECT si2.name 
                FROM `tabSales Invoice` si2
                INNER JOIN `tabSales Invoice Item` sii ON si2.name = sii.parent
                INNER JOIN `tabAddress` addr2 ON si2.customer_address = addr2.name
                WHERE sii.item_code IN (SELECT name FROM `tabItem` WHERE item_group = 'Products')
                AND addr2.country NOT IN ({1})
            )
        )
    """.format(template_placeholders, eu_placeholder_list)
    
    # Build parameters list
    params = [from_date, to_date, company] + exempt_templates + eu_countries + eu_countries
    
    # Execute query
    out_of_scope = frappe.db.sql(query, params, as_dict=1)
    
    # Return result
    return flt(out_of_scope[0].amount) if out_of_scope and out_of_scope[0].amount is not None else 0

def get_eu_goods_acquisitions(company, from_date, to_date):
    # Get EU countries list
    eu_countries = get_eu_countries()
    
    # Get service item groups to exclude
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(
            CASE WHEN pi.is_return = 0 THEN pi.base_net_total ELSE -pi.base_net_total END
        ) as amount
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        INNER JOIN `tabAddress` addr ON pi.supplier_address = addr.name
        INNER JOIN `tabSupplier` supp ON pi.supplier = supp.name
        INNER JOIN `tabItem` item ON pii.item_code = item.name
        WHERE pi.posting_date BETWEEN %s AND %s
        AND pi.company = %s
        AND pi.docstatus = 1
        AND addr.country IN ({0})
        AND addr.country != 'Cyprus'
        AND supp.supplier_type = 'Company'
        AND item.item_group NOT IN ({1})
    """.format(placeholder_list, service_placeholders)
    
    params = [from_date, to_date, company] + eu_countries + (service_groups if service_groups else [])
    eu_goods = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_eu_services_acquisitions(company, from_date, to_date):
    # Get EU countries list using utility function
    eu_countries = get_eu_countries()
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(
            CASE WHEN pi.is_return = 0 THEN pi.base_net_total ELSE -pi.base_net_total END
        ) as amount
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        INNER JOIN `tabAddress` addr ON pi.supplier_address = addr.name
        INNER JOIN `tabSupplier` supp ON pi.supplier = supp.name
        AND supp.supplier_type = 'Company'
        WHERE pi.posting_date BETWEEN %s AND %s
        AND pi.company = %s
        AND pi.docstatus = 1
        AND addr.country IN ({0})
        AND addr.country != 'Cyprus'
        AND pii.item_code IN (
            SELECT name FROM `tabItem` WHERE item_group = 'Services'
        )
    """.format(placeholder_list)
    
    # Build parameters list - add EU countries to the parameters
    params = [from_date, to_date, company] + eu_countries
    
    eu_services = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

@frappe.whitelist()
def export_vat_return(filters):
    """
    Export VAT return in the format required by Cyprus tax authorities
    """
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)
    
    # Get the tax ID from the company - no longer passed as a filter
    company = filters.get('company')
    tax_id = frappe.db.get_value("Company", company, "tax_id")
    
    # Ensure dates are set if using fiscal_year and quarter
    if not filters.get('from_date') or not filters.get('to_date'):
        fiscal_year = filters.get('fiscal_year')
        quarter = filters.get('quarter')
        if fiscal_year and quarter:
            dates = get_quarter_dates(fiscal_year, quarter)
            filters['from_date'] = dates['from_date']
            filters['to_date'] = dates['to_date']
    
    # Generate the file content based on Cyprus Tax Authority requirements
    content = "Cyprus VAT Return\n"
    content += f"Company: {company}\n"
    content += f"Tax ID: {tax_id}\n"
    content += f"Period: {filters.get('from_date')} to {filters.get('to_date')}\n\n"
    
    # Add VAT details - actual implementation would format this according to Cyprus tax authority specs
    data = get_data(filters)
    for row in data:
        content += f"{row['vat_field']}: {row['description']}: {row['amount']}\n"
    
    # Save the file
    file_name = f"cyprus_vat_return_{filters.get('from_date')}_{filters.get('to_date')}.txt"
    file_url = frappe.utils.file_manager.save_file(
        file_name, 
        content, 
        "Company", 
        company, 
        is_private=1
    )
    
    return file_url.get('file_url')

def get_service_item_groups():
    """Get all item groups that represent services (Professional Services, Digital Services and their children)"""
    service_groups = []
    
    # Get Professional Services and all its children
    prof_services = frappe.get_all("Item Group", 
        filters={"name": ["in", ["Professional Services", "Digital Services"]]},
        fields=["name"])
    
    # Add the root service groups
    service_groups.extend([d.name for d in prof_services])
    
    # Get all children of service groups
    for service_group in service_groups.copy():  # Use copy to avoid modifying during iteration
        children = frappe.get_all("Item Group", 
            filters={"parent_item_group": service_group},
            fields=["name"])
        service_groups.extend([d.name for d in children])
    
    return service_groups