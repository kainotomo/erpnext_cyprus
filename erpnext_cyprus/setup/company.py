import frappe
from frappe import _

@frappe.whitelist()
def setup_cyprus_company(company=None):
    # Set default accounts
    set_cyprus_default_accounts(company)

    # Create purchase tax templates
    create_purchase_tax_templates(company)

    frappe.msgprint(_("Setup completed for company: {0}").format(company))

def set_cyprus_default_accounts(company_name):
    """
    Set default accounts for a Cyprus company when triggered by the user.
    """
    company = frappe.get_doc("Company", company_name)

    # Ensure the company is in Cyprus and uses a Cyprus chart of accounts
    if company.country != "Cyprus" or not company.chart_of_accounts or "Cyprus" not in company.chart_of_accounts:
        frappe.throw(_("This action is only applicable for Cyprus companies using a Cyprus chart of accounts."))

    # Set default accounts
    defaults = get_cyprus_default_accounts(company.name)
    for account_field, account_name in defaults.items():
        company.set(account_field, account_name)

    company.flags.ignore_mandatory = True
    company.save()

def get_cyprus_default_accounts(company_name):
    """
    Get default accounts for Cyprus companies based on the chart of accounts.
    """
    company_abbr = frappe.get_cached_value("Company", company_name, "abbr")

    # Map account names to fields in the Company doctype
    defaults = {
        "default_bank_account": find_account("Bank Account - Current", company_name),
        "default_cash_account": find_account("Petty Cash", company_name),
        "default_receivable_account": find_account("Domestic Customers", company_name),
        "default_payable_account": find_account("Domestic Suppliers", company_name),
        "default_income_account": find_account("Domestic Sales", company_name),
        "default_expense_account": find_account("Domestic COGS", company_name),
        "default_inventory_account": find_account("Stores", company_name),
        "stock_adjustment_account": find_account("Stock Adjustment", company_name),
        "stock_received_but_not_billed": find_account("Stock Received But Not Billed", company_name),
        "exchange_gain_loss_account": find_account("Foreign Exchange Gains", company_name),
        "round_off_account": find_account("Miscellaneous Expenses", company_name),
    }

    return defaults

def find_account(account_name, company_name):
    """
    Find an account by name or pattern.
    """
    account = frappe.db.get_value(
        "Account",
        {"account_name": account_name, "company": company_name},
        "name"
    )

    if not account:
        accounts = frappe.db.sql("""
            SELECT name FROM `tabAccount`
            WHERE company=%s AND account_name LIKE %s
            ORDER BY lft LIMIT 1
        """, (company_name, f"%{account_name}%"), as_dict=True)

        if accounts:
            account = accounts[0].name

    return account

def create_purchase_tax_templates(company):
    """
    Create purchase tax templates for a Cyprus company.
    
    This function creates various tax templates required for purchase transactions,
    covering all possible tax scenarios for a Cyprus company.
    
    Args:
        company (str): The name of the company
    
    Returns:
        bool: True if templates were created, False otherwise
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Ensure company is in Cyprus
    if frappe.db.get_value("Company", company, "country") != "Cyprus":
        frappe.msgprint(_("Purchase tax templates can only be created for Cyprus companies."))
        return False
    
    # Define purchase tax templates
    templates = [
        # Standard domestic rates
        {
            "title": "Cyprus Purchase VAT 19%",
            "is_default": 1,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Cyprus Standard Rate VAT Input (19%) - {company_abbr}",
                "description": "VAT 19%",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        {
            "title": "Cyprus Purchase VAT 9%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Cyprus Reduced Rate VAT Input (9%) - {company_abbr}",
                "description": "VAT 9%",
                "add_deduct_tax": "Add",
                "rate": 9
            }]
        },
        {
            "title": "Cyprus Purchase VAT 5%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Cyprus Reduced Rate VAT Input (5%) - {company_abbr}",
                "description": "VAT 5%",
                "add_deduct_tax": "Add",
                "rate": 5
            }]
        },
        {
            "title": "Cyprus Purchase VAT 0% (Zero Rated)",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"VAT Control - {company_abbr}",
                "description": "VAT 0% - Zero Rate",
                "rate": 0
            }]
        },
        {
            "title": "Cyprus Purchase VAT Exempt",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"VAT Control - {company_abbr}",
                "description": "VAT Exempt",
                "rate": 0
            }]
        },
        
        # EU purchases
        {
            "title": "EU Purchase - Goods - Reverse Charge",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Reverse Charge VAT Output - {company_abbr}",
                    "description": "VAT 19% - Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Acquisition VAT Input - {company_abbr}",
                    "description": "VAT 19% - Reverse Charge Input",
                    "add_deduct_tax": "Deduct",
                    "rate": 19
                }
            ]
        },
        {
            "title": "EU Purchase - Services - Reverse Charge",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Reverse Charge VAT Output - {company_abbr}",
                    "description": "VAT 19% - Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Acquisition VAT Input - {company_abbr}",
                    "description": "VAT 19% - Reverse Charge Input",
                    "add_deduct_tax": "Deduct",
                    "rate": 19
                }
            ]
        },
        
        # Non-EU purchases
        {
            "title": "Import with VAT",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Import VAT Input - {company_abbr}",
                "description": "Import VAT 19%",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        
        # Special cases
        {
            "title": "Purchase with Non-Deductible VAT",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"Non-Deductible VAT - {company_abbr}",
                "description": "Non-Deductible VAT 19%",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        {
            "title": "Purchase with Partial VAT Deduction (50%)",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": f"Cyprus Standard Rate VAT Input (19%) - {company_abbr}",
                    "description": "Deductible VAT 19% (50%)",
                    "add_deduct_tax": "Add",
                    "rate": 9.5
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": f"Non-Deductible VAT - {company_abbr}",
                    "description": "Non-Deductible VAT 19% (50%)",
                    "add_deduct_tax": "Add",
                    "rate": 9.5
                }
            ]
        },
        {
            "title": "Purchase - Triangulation",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": f"VAT Control - {company_abbr}",
                "description": "VAT 0% - Triangulation",
                "rate": 0
            }]
        },
        
        # Digital services specific (from your prompt)
        {
            "title": "EU Digital Services - Reverse Charge",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Reverse Charge VAT Output - {company_abbr}",
                    "description": "VAT 19% - Digital Services Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Acquisition VAT Input - {company_abbr}",
                    "description": "VAT 19% - Digital Services Reverse Charge Input",
                    "add_deduct_tax": "Deduct",
                    "rate": 19
                }
            ]
        },
        {
            "title": "Non-EU Digital Services - Reverse Charge",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Reverse Charge VAT Output - {company_abbr}",
                    "description": "VAT 19% - Digital Services Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": f"EU Acquisition VAT Input - {company_abbr}",
                    "description": "VAT 19% - Digital Services Reverse Charge Input",
                    "add_deduct_tax": "Deduct",
                    "rate": 19
                }
            ]
        }
    ]
    
    # Create the tax templates
    created_count = 0
    for template in templates:
        if create_purchase_tax_template(company, template):
            created_count += 1
    
    if created_count > 0:
        return True
    else:
        return False

def create_purchase_tax_template(company, template_data):
    """
    Create a single purchase tax template if it doesn't already exist.
    
    Args:
        company (str): The company name
        template_data (dict): Template data including title and taxes
    
    Returns:
        bool: True if created, False if already exists
    """
    title = template_data["title"]
    is_default = template_data.get("is_default", 0)
    taxes = template_data["taxes"]
    
    # Check if template already exists
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    template_name = f"{title} - {company_abbr}"
    
    if frappe.db.exists("Purchase Taxes and Charges Template", template_name):
        return False
        
    # Create new template
    doc = frappe.new_doc("Purchase Taxes and Charges Template")
    doc.title = title
    doc.company = company
    doc.is_default = is_default
    
    # Add tax entries
    for tax_entry in taxes:
        doc.append("taxes", {
            "charge_type": tax_entry["charge_type"],
            "account_head": tax_entry["account_head"],
            "description": tax_entry["description"],
            "rate": tax_entry["rate"],
            "add_deduct_tax": tax_entry.get("add_deduct_tax", "Add")
        })
    
    try:
        doc.save()
        return True
    except Exception as e:
        frappe.log_error(f"Error creating tax template {title}: {str(e)}", "ERPNext Cyprus Setup Error")
        return False