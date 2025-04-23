# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_first_day, get_last_day, add_days, add_months
from erpnext_cyprus.utils.tax_utils import get_cyprus_tax_accounts

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
    output_vat = get_output_vat(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 1"),
        "description": _("VAT due on sales and other outputs"),
        "amount": output_vat
    })

    # Box 2: VAT due on acquisitions from EU countries
    eu_acquisitions_vat = get_eu_acquisitions_vat(company, from_date, to_date)
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
    input_vat = get_input_vat(company, from_date, to_date)
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
    total_sales = get_total_sales(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 6"),
        "description": _("Total value of sales and other outputs excluding VAT"),
        "amount": total_sales
    })
    
    # Box 7: Total value of purchases and inputs excluding VAT
    total_purchases = get_total_purchases(company, from_date, to_date)
    vat_return_data.append({
        "vat_field": _("Box 7"),
        "description": _("Total value of purchases and inputs excluding VAT"),
        "amount": total_purchases
    })
    
    # Box 8A & 8B: EU goods and services supplies
    eu_supplies_goods = get_eu_goods_supplies(company, from_date, to_date)
    eu_supplies_services = get_eu_services_supplies(company, from_date, to_date)
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

def get_output_vat(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get all output VAT accounts
    output_vat_accounts = [
        tax_accounts["vat_local_19"],
        tax_accounts["vat_reduced_9"],
        tax_accounts["vat_super_reduced_5"]
    ]
    
    # Format for SQL IN clause - converting to a proper list of parameters
    placeholder_list = ', '.join(['%s'] * len(output_vat_accounts))
    
    # Build query with proper parameterization for all values
    query = """
        SELECT SUM(credit - debit) as vat_amount
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND account IN ({0})
    """.format(placeholder_list)
    
    # Build parameters list - add account names to the parameters
    params = [from_date, to_date, company] + output_vat_accounts
    
    # Execute the query with all parameters
    output_vat = frappe.db.sql(query, params, as_dict=1)
    
    return flt(output_vat[0].vat_amount) if output_vat and output_vat[0].vat_amount is not None else 0

def get_input_vat(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get input VAT accounts - using import_vat and any other input accounts
    input_vat_accounts = []
    
    # Add import VAT account if available
    if "import_vat" in tax_accounts:
        input_vat_accounts.append(tax_accounts["import_vat"])
    
    # If no specific input accounts are found in tax_utils, fall back to a generic search
    if not input_vat_accounts:
        input_vat = frappe.db.sql("""
            SELECT SUM(debit - credit) as vat_amount
            FROM `tabGL Entry`
            WHERE posting_date BETWEEN %s AND %s
            AND company = %s
            AND account IN (
                SELECT name FROM `tabAccount`
                WHERE account_type = 'Tax' AND account_name LIKE '%%Input%%'
                AND company = %s
            )
        """, (from_date, to_date, company, company), as_dict=1)
        
        return flt(input_vat[0].vat_amount) if input_vat and input_vat[0].vat_amount is not None else 0
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(input_vat_accounts))
    
    # Build query with proper parameterization for all values
    query = """
        SELECT SUM(debit - credit) as vat_amount
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND account IN ({0})
    """.format(placeholder_list)
    
    # Build parameters list - add account names to the parameters
    params = [from_date, to_date, company] + input_vat_accounts
    
    input_vat = frappe.db.sql(query, params, as_dict=1)
    
    return flt(input_vat[0].vat_amount) if input_vat and input_vat[0].vat_amount is not None else 0

def get_eu_acquisitions_vat(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Get EU acquisition VAT accounts
    eu_vat_accounts = []
    
    # Add intra-EU acquisition account if available
    if "intra_eu_acquisition" in tax_accounts:
        eu_vat_accounts.append(tax_accounts["intra_eu_acquisition"])
    
    # Add reverse charge services account if available
    if "reverse_charge_services" in tax_accounts:
        eu_vat_accounts.append(tax_accounts["reverse_charge_services"])
    
    # If no specific EU VAT accounts are found in tax_utils, fall back to a generic search
    if not eu_vat_accounts:
        eu_vat = frappe.db.sql("""
            SELECT SUM(credit) as vat_amount
            FROM `tabGL Entry`
            WHERE posting_date BETWEEN %s AND %s
            AND company = %s
            AND account IN (
                SELECT name FROM `tabAccount`
                WHERE account_type = 'Tax' AND account_name LIKE '%%Acquisition%%'
                AND company = %s
            )
        """, (from_date, to_date, company, company), as_dict=1)
        
        return flt(eu_vat[0].vat_amount) if eu_vat and eu_vat[0].vat_amount is not None else 0
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_vat_accounts))
    
    # Build query with proper parameterization for all values
    query = """
        SELECT SUM(credit) as vat_amount
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND account IN ({0})
    """.format(placeholder_list)
    
    # Build parameters list - add account names to the parameters
    params = [from_date, to_date, company] + eu_vat_accounts
    
    eu_vat = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_vat[0].vat_amount) if eu_vat and eu_vat[0].vat_amount is not None else 0

def get_total_sales(company, from_date, to_date):
    # Get total sales excluding VAT
    sales = frappe.db.sql("""
        SELECT SUM(base_net_total) as amount
        FROM `tabSales Invoice`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND docstatus = 1
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(sales[0].amount) if sales and sales[0].amount is not None else 0

def get_total_purchases(company, from_date, to_date):
    # Get total purchases excluding VAT
    purchases = frappe.db.sql("""
        SELECT SUM(base_net_total) as amount
        FROM `tabPurchase Invoice`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND docstatus = 1
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(purchases[0].amount) if purchases and purchases[0].amount is not None else 0

def get_eu_goods_supplies(company, from_date, to_date):
    # EU goods supplies (exports to EU)
    eu_goods = frappe.db.sql("""
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabCustomer` c ON si.customer = c.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND c.territory IN (
            SELECT name FROM `tabTerritory` 
            WHERE parent_territory = 'European Union'
            AND name != 'Cyprus'
        )
        AND sii.item_code IN (
            SELECT name FROM `tabItem` WHERE item_group = 'Products'
        )
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_eu_services_supplies(company, from_date, to_date):
    # EU services supplies
    eu_services = frappe.db.sql("""
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
        INNER JOIN `tabCustomer` c ON si.customer = c.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND c.territory IN (
            SELECT name FROM `tabTerritory` 
            WHERE parent_territory = 'European Union'
            AND name != 'Cyprus'
        )
        AND sii.item_code IN (
            SELECT name FROM `tabItem` WHERE item_group = 'Services'
        )
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_non_eu_exports(company, from_date, to_date):
    # Non-EU exports
    exports = frappe.db.sql("""
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabCustomer` c ON si.customer = c.name
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND c.territory NOT IN (
            SELECT name FROM `tabTerritory` 
            WHERE parent_territory = 'European Union'
        )
        AND c.territory != 'Cyprus'
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(exports[0].amount) if exports and exports[0].amount is not None else 0

def get_out_of_scope_sales(company, from_date, to_date):
    # Out of scope sales (zero-rated, exempt)
    out_of_scope = frappe.db.sql("""
        SELECT SUM(si.base_net_total) as amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Taxes and Charges` stc ON si.name = stc.parent
        WHERE si.posting_date BETWEEN %s AND %s
        AND si.company = %s
        AND si.docstatus = 1
        AND stc.rate = 0
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(out_of_scope[0].amount) if out_of_scope and out_of_scope[0].amount is not None else 0

def get_eu_goods_acquisitions(company, from_date, to_date):
    # Get EU countries list using utility function if available
    try:
        from erpnext_cyprus.utils.tax_utils import get_eu_countries
        eu_countries = get_eu_countries()
    except (ImportError, AttributeError):
        # Fallback to hardcoded list if function not available
        eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Czech Republic", 
                        "Denmark", "Estonia", "Finland", "France", "Germany", 
                        "Greece", "Hungary", "Ireland", "Italy", "Latvia", 
                        "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland", 
                        "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"]
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper parameterization for all values
    query = """
        SELECT SUM(pi.base_net_total) as amount
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        INNER JOIN `tabSupplier` s ON pi.supplier = s.name
        WHERE pi.posting_date BETWEEN %s AND %s
        AND pi.company = %s
        AND pi.docstatus = 1
        AND s.country IN ({0})
        AND s.country != 'Cyprus'
        AND pii.item_code IN (
            SELECT name FROM `tabItem` WHERE item_group = 'Products'
        )
    """.format(placeholder_list)
    
    # Build parameters list - add EU countries to the parameters
    params = [from_date, to_date, company] + eu_countries
    
    eu_goods = frappe.db.sql(query, params, as_dict=1)
    
    return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_eu_services_acquisitions(company, from_date, to_date):
    # EU services acquisitions
    eu_countries = ["Austria", "Belgium", "Bulgaria", "Croatia", "Czech Republic", 
                    "Denmark", "Estonia", "Finland", "France", "Germany", 
                    "Greece", "Hungary", "Ireland", "Italy", "Latvia", 
                    "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland", 
                    "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden"]
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper parameterization for all values
    query = """
        SELECT SUM(pi.base_net_total) as amount
        FROM `tabPurchase Invoice` pi
        INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        INNER JOIN `tabSupplier` s ON pi.supplier = s.name
        WHERE pi.posting_date BETWEEN %s AND %s
        AND pi.company = %s
        AND pi.docstatus = 1
        AND s.country IN ({0})
        AND s.country != 'Cyprus'
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