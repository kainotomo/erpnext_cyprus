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
    
    # Query 1: Standard domestic VAT from Sales Invoices and Journal Entries
    query1 = """
        SELECT SUM(
            CASE 
                WHEN voucher_type IN ('Sales Invoice') THEN credit
                WHEN voucher_type IN ('Sales Invoice Credit Note') THEN -debit
                WHEN voucher_type IN ('Journal Entry') AND credit > 0 THEN credit
                WHEN voucher_type IN ('Journal Entry') AND debit > 0 THEN -debit
                ELSE 0
            END
        ) as vat_amount
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND account IN ({0})
        AND is_cancelled = 0
        AND docstatus = 1
    """.format(placeholder_list)
    
    # Build parameters list for query1
    params1 = [from_date, to_date, company] + output_vat_accounts
    
    # Execute query1
    output_vat_result = frappe.db.sql(query1, params1, as_dict=1)
    output_vat = flt(output_vat_result[0].vat_amount) if output_vat_result and output_vat_result[0].vat_amount is not None else 0
    
    # Get EU countries to exclude them
    eu_countries = get_eu_countries()
    eu_placeholders = ', '.join(['%s'] * len(eu_countries))
    
    # Get all service item groups (parent groups and their children)
    service_parent_groups = ["Professional Services", "Digital Services"]
    all_service_groups = []
    
    # First add the parent groups
    all_service_groups.extend(service_parent_groups)
    
    # Then find and add all child groups
    for parent_group in service_parent_groups:
        child_groups = frappe.get_all(
            "Item Group", 
            filters={"parent_item_group": parent_group},
            fields=["item_group_name"]
        )
        all_service_groups.extend([group.item_group_name for group in child_groups])
    
    # Create placeholders for the service groups
    service_placeholders = ', '.join(['%s'] * len(all_service_groups)) if all_service_groups else "''"
    
    # Query 2: Reverse charge VAT on services from non-EU suppliers
    query2 = """
        SELECT SUM(
            CASE 
                WHEN gle.voucher_type = 'Purchase Invoice' THEN gle.credit
                WHEN gle.voucher_type = 'Purchase Invoice Debit Note' THEN -gle.debit
                ELSE 0
            END
        ) as vat_amount
        FROM `tabGL Entry` gle
        INNER JOIN `tabPurchase Invoice` pi ON gle.voucher_no = pi.name 
            AND (gle.voucher_type = 'Purchase Invoice' OR gle.voucher_type = 'Purchase Invoice Debit Note')
        INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
        INNER JOIN `tabItem` item ON pii.item_code = item.name
        LEFT JOIN `tabAddress` addr ON pi.supplier_address = addr.name
        WHERE gle.posting_date BETWEEN %s AND %s
        AND gle.company = %s
        AND gle.account IN ({0})
        AND (
            (gle.voucher_type = 'Purchase Invoice' AND gle.credit > 0) OR
            (gle.voucher_type = 'Purchase Invoice Debit Note' AND gle.debit > 0)
        )
        AND gle.is_cancelled = 0
        AND gle.docstatus = 1
        AND (
            (addr.country IS NOT NULL AND addr.country NOT IN ({1}) AND addr.country != 'Cyprus')
            OR
            pi.taxes_and_charges = 'Non-EU Import VAT'
        )
        AND item.item_group IN ({2})
    """.format(placeholder_list, eu_placeholders, service_placeholders)
    
    # Build parameters list for query2
    params2 = [from_date, to_date, company] + output_vat_accounts + eu_countries + all_service_groups
    
    # Execute query2 only if we have service groups
    non_eu_service_vat = 0
    if all_service_groups:
        non_eu_service_vat_result = frappe.db.sql(query2, params2, as_dict=1)
        non_eu_service_vat = flt(non_eu_service_vat_result[0].vat_amount) if non_eu_service_vat_result and non_eu_service_vat_result[0].vat_amount is not None else 0
    
    # Return combined VAT amount
    return output_vat + non_eu_service_vat

def get_input_vat(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        return 0
    
    # Regular input VAT accounts
    vat_accounts = [
        tax_accounts["vat"]
    ]
    
    # Filter out None values (accounts that might not exist)
    vat_accounts = [acc for acc in vat_accounts if acc]
    
    if not vat_accounts:
        return 0
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(vat_accounts))
    
    # Query for regular input VAT (filtered by voucher_type)
    query1 = """
        SELECT SUM(
            CASE 
                WHEN voucher_type IN ('Purchase Invoice') THEN debit
                WHEN voucher_type IN ('Purchase Invoice Debit Note') THEN -credit
                ELSE 0
            END
        ) as vat_amount
        FROM `tabGL Entry`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND account IN ({0})
    """.format(placeholder_list)
    
    params1 = [from_date, to_date, company] + vat_accounts
    regular_vat = frappe.db.sql(query1, params1, as_dict=1)
    
    # Get reverse charge VAT accounts
    rc_accounts = []
    if "intra_eu_acquisition" in tax_accounts and tax_accounts["intra_eu_acquisition"]:
        rc_accounts.append(tax_accounts["intra_eu_acquisition"])
    if "reverse_charge_services" in tax_accounts and tax_accounts["reverse_charge_services"]:
        rc_accounts.append(tax_accounts["reverse_charge_services"])
    
    # Calculate reverse charge input VAT (where VAT is both paid and reclaimed)
    rc_vat_amount = 0
    if rc_accounts:
        rc_placeholder_list = ', '.join(['%s'] * len(rc_accounts))
        query2 = """
            SELECT SUM(
                CASE 
                    WHEN voucher_type IN ('Purchase Invoice') THEN debit
                    WHEN voucher_type IN ('Purchase Invoice Debit Note') THEN -credit
                    ELSE 0
                END
            ) as vat_amount
            FROM `tabGL Entry`
            WHERE posting_date BETWEEN %s AND %s
            AND company = %s
            AND account IN ({0})
        """.format(rc_placeholder_list)
        
        params2 = [from_date, to_date, company] + rc_accounts
        rc_vat = frappe.db.sql(query2, params2, as_dict=1)
        rc_vat_amount = flt(rc_vat[0].vat_amount) if rc_vat and rc_vat[0].vat_amount is not None else 0
    
    # Combine regular and reverse charge VAT
    total_vat = flt(regular_vat[0].vat_amount) if regular_vat and regular_vat[0].vat_amount is not None else 0
    return total_vat + rc_vat_amount

def get_eu_acquisitions_vat(company, from_date, to_date):
    # Get the Cyprus tax accounts
    tax_accounts = get_tax_accounts(company)
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
    
    # If no specific EU VAT accounts are found, fall back to a generic search
    if not eu_vat_accounts:
        eu_vat = frappe.db.sql("""
            SELECT SUM(
                CASE 
                    WHEN voucher_type IN ('Purchase Invoice') THEN credit
                    WHEN voucher_type IN ('Purchase Invoice Debit Note') THEN -debit
                    ELSE 0
                END
            ) as vat_amount
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
    
    query = """
        SELECT SUM(
            CASE 
                WHEN voucher_type IN ('Purchase Invoice') THEN credit
                WHEN voucher_type IN ('Purchase Invoice Debit Note') THEN -debit
                ELSE 0
            END
        ) as vat_amount
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
    # Get total sales excluding VAT (including credit notes)
    sales = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN is_return = 0 THEN base_net_total ELSE -base_net_total END) as amount
        FROM `tabSales Invoice`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND docstatus = 1
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(sales[0].amount) if sales and sales[0].amount is not None else 0

def get_total_purchases(company, from_date, to_date):
    # Get total purchases excluding VAT (including debit notes)
    purchases = frappe.db.sql("""
        SELECT 
            SUM(CASE WHEN is_return = 0 THEN base_net_total ELSE -base_net_total END) as amount
        FROM `tabPurchase Invoice`
        WHERE posting_date BETWEEN %s AND %s
        AND company = %s
        AND docstatus = 1
    """, (from_date, to_date, company), as_dict=1)
    
    return flt(purchases[0].amount) if purchases and purchases[0].amount is not None else 0

def get_eu_goods_supplies(company, from_date, to_date):
    # Get EU countries list using utility function
    eu_countries = get_eu_countries()
    
    # Get service item groups to exclude
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(
            CASE WHEN si.is_return = 0 THEN si.base_net_total ELSE -si.base_net_total END
        ) as amount
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

def get_eu_services_supplies(company, from_date, to_date):
    # Get EU countries list using utility function
    eu_countries = get_eu_countries()
    
    # Get service item groups
    service_groups = get_service_item_groups()
    service_placeholders = ', '.join(['%s'] * len(service_groups)) if service_groups else "''"
    
    # Format for SQL IN clause
    placeholder_list = ', '.join(['%s'] * len(eu_countries))
    
    # Build query with proper address relationships
    query = """
        SELECT SUM(
            CASE WHEN si.is_return = 0 THEN si.base_net_total ELSE -si.base_net_total END
        ) as amount
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