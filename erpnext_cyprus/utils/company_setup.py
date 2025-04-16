import frappe
from frappe import _

def auto_setup_cyprus_company(doc, method):
    """
    Automatically run Cyprus company setup when a Cyprus company is created
    and its chart of accounts is set up.
    
    This function is triggered by the on_update hook for the Company doctype.
    """
    # Check if this is a Cyprus company
    if doc.country != "Cyprus":
        return
        
    # Check if chart of accounts exists
    if not doc.chart_of_accounts or "Cyprus" not in doc.chart_of_accounts:
        return
        
    # Check if default accounts are set up
    if not doc.default_receivable_account or not doc.default_payable_account:
        return
        
    # Check if company has already been set up
    setup_flag_key = f"cyprus_company_setup_done_{doc.name}"
    if frappe.cache().get_value(setup_flag_key):
        return
        
    try:
        # Run the Cyprus company setup
        setup_cyprus_company(doc.name)
        
        # Set a flag in cache to prevent re-running
        frappe.cache().set_value(setup_flag_key, True)
        
    except Exception as e:
        frappe.log_error(f"Error in auto setup for Cyprus company {doc.name}: {str(e)}", 
                        "Cyprus Company Auto Setup Error")
        
@frappe.whitelist()
def setup_cyprus_company(company=None):

    check_account = find_account("Cyprus Standard Rate VAT Output (19%)", company)
    if not check_account:
        frappe.throw(_("Cyprus Standard Rate VAT Output (19%) account not found in the chart of accounts."))

    # Set default accounts
    set_cyprus_default_accounts(company)

    # Create purchase tax templates
    create_purchase_tax_templates(company)

    # Create sales tax templates
    create_sales_tax_templates(company)

    # Create tax rules
    create_cyprus_tax_rules(company)

    # Create sales tax rules
    create_cyprus_sales_tax_rules(company)

    frappe.msgprint(_("Setup completed for company: {0}").format(company))

def set_cyprus_default_accounts(company_name):
    """
    Set default accounts for a Cyprus company when triggered by the user.
    """
    company = frappe.get_doc("Company", company_name)

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
        "default_income_account": find_account("Goods - Standard Rate (19%)", company_name),
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
    Find an account by name or pattern, handling numbered chart of accounts.
    """
    # Try exact match first
    account = frappe.db.get_value(
        "Account",
        {"account_name": account_name, "company": company_name},
        "name"
    )

    if not account:
        # Try to find with account number prefix (for numbered charts of accounts)
        accounts = frappe.db.sql("""
            SELECT name FROM `tabAccount`
            WHERE company=%s 
            AND (
                account_name LIKE %s 
                OR name LIKE %s 
                OR CONCAT(account_number, ' - ', account_name) LIKE %s
            )
            ORDER BY lft LIMIT 1
        """, (company_name, f"%{account_name}%", f"%{account_name}%", f"%{account_name}%"), as_dict=True)

        if accounts:
            account = accounts[0].name
            
        # If it's a tax account but still not found, try with account_type filter
        if not account and ("VAT" in account_name or "Tax" in account_name):
            accounts = frappe.db.sql("""
                SELECT name FROM `tabAccount`
                WHERE company=%s 
                AND account_type='Tax'
                AND (
                    account_name LIKE %s 
                    OR name LIKE %s
                )
                ORDER BY lft LIMIT 1
            """, (company_name, f"%{account_name}%", f"%{account_name}%"), as_dict=True)
            
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
        return False
    
    # Define purchase tax templates
    templates = [
        # Standard domestic rates
        {
            "title": "Cyprus Purchase VAT 19%",
            "is_default": 1,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Standard Rate VAT Input (19%)", company),
                "description": "VAT 19%",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        {
            "title": "Cyprus Purchase VAT 9%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Reduced Rate VAT Input (9%)", company),
                "description": "VAT 9%",
                "add_deduct_tax": "Add",
                "rate": 9
            }]
        },
        {
            "title": "Cyprus Purchase VAT 5%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Reduced Rate VAT Input (5%)", company),
                "description": "VAT 5%",
                "add_deduct_tax": "Add",
                "rate": 5
            }]
        },
        {
            "title": "Cyprus Purchase VAT 0% (Zero Rated)",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Zero Rate",
                "rate": 0
            }]
        },
        {
            "title": "Cyprus Purchase VAT Exempt",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
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
                    "account_head": find_account("EU Reverse Charge VAT Output", company),
                    "description": "VAT 19% - Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("EU Acquisition VAT Input", company),
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
                    "account_head": find_account("EU Reverse Charge VAT Output", company),
                    "description": "VAT 19% - Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("EU Acquisition VAT Input", company),
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
                "account_head": find_account("Import VAT Input", company),
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
                "account_head": find_account("Non-Deductible VAT", company),
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
                    "account_head": find_account("Cyprus Standard Rate VAT Input (19%)", company),
                    "description": "Deductible VAT 19% (50%)",
                    "add_deduct_tax": "Add",
                    "rate": 9.5
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("Non-Deductible VAT", company),
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
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Triangulation",
                "rate": 0
            }]
        },
        
        # Digital services specific
        {
            "title": "EU Digital Services - Reverse Charge",
            "taxes": [
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("EU Reverse Charge VAT Output", company),
                    "description": "VAT 19% - Digital Services Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("EU Acquisition VAT Input", company),
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
                    "account_head": find_account("EU Reverse Charge VAT Output", company),
                    "description": "VAT 19% - Digital Services Reverse Charge Output",
                    "add_deduct_tax": "Add",
                    "rate": 19
                },
                {
                    "charge_type": "On Net Total",
                    "account_head": find_account("EU Acquisition VAT Input", company),
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

def create_sales_tax_templates(company):
    """
    Create sales tax templates for a Cyprus company.
    
    This function creates various tax templates required for sales transactions,
    covering all possible tax scenarios for a Cyprus company.
    
    Args:
        company (str): The name of the company
    
    Returns:
        bool: True if templates were created, False otherwise
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Ensure company is in Cyprus
    if frappe.db.get_value("Company", company, "country") != "Cyprus":
        return False
    
    # Define EU country VAT rates and codes
    eu_country_rates = {
        "Austria": {"rate": 20, "code": "AT"},
        "Belgium": {"rate": 21, "code": "BE"},
        "Bulgaria": {"rate": 20, "code": "BG"},
        "Croatia": {"rate": 25, "code": "HR"},
        "Czech Republic": {"rate": 21, "code": "CZ"},
        "Denmark": {"rate": 25, "code": "DK"},
        "Estonia": {"rate": 20, "code": "EE"},
        "Finland": {"rate": 24, "code": "FI"},
        "France": {"rate": 20, "code": "FR"},
        "Germany": {"rate": 19, "code": "DE"},
        "Greece": {"rate": 24, "code": "GR"},
        "Hungary": {"rate": 27, "code": "HU"},
        "Ireland": {"rate": 23, "code": "IE"},
        "Italy": {"rate": 22, "code": "IT"},
        "Latvia": {"rate": 21, "code": "LV"},
        "Lithuania": {"rate": 21, "code": "LT"},
        "Luxembourg": {"rate": 17, "code": "LU"},
        "Malta": {"rate": 18, "code": "MT"},
        "Netherlands": {"rate": 21, "code": "NL"},
        "Poland": {"rate": 23, "code": "PL"},
        "Portugal": {"rate": 23, "code": "PT"},
        "Romania": {"rate": 19, "code": "RO"},
        "Slovakia": {"rate": 20, "code": "SK"},
        "Slovenia": {"rate": 22, "code": "SI"},
        "Spain": {"rate": 21, "code": "ES"},
        "Sweden": {"rate": 25, "code": "SE"}
    }
    
    # Define base templates (domestic and non-EU)
    templates = [
        # Domestic sales
        {
            "title": "Cyprus Sales VAT 19%",
            "is_default": 1,
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Standard Rate VAT Output (19%)", company),
                "description": "VAT 19%",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        {
            "title": "Cyprus Sales VAT 9%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Reduced Rate VAT Output (9%)", company),
                "description": "VAT 9%",
                "add_deduct_tax": "Add",
                "rate": 9
            }]
        },
        {
            "title": "Cyprus Sales VAT 5%",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Reduced Rate VAT Output (5%)", company),
                "description": "VAT 5%",
                "add_deduct_tax": "Add",
                "rate": 5
            }]
        },
        {
            "title": "Cyprus Sales VAT 0% (Zero Rated)",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Zero Rate",
                "rate": 0
            }]
        },
        {
            "title": "Cyprus Sales VAT Exempt",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT Exempt",
                "rate": 0
            }]
        },
        
        # EU B2B sales
        {
            "title": "EU B2B Goods - Zero Rated",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Reverse Charge - Art. 138 EU VAT Directive",
                "rate": 0
            }]
        },
        {
            "title": "EU B2B Services - Zero Rated",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Reverse Charge - Art. 44 EU VAT Directive",
                "rate": 0
            }]
        },
        
        # EU B2C threshold sales
        {
            "title": "EU B2C Goods - Below Threshold",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Standard Rate VAT Output (19%)", company),
                "description": "Cyprus VAT 19% (Below Distance Selling Threshold)",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        },
        
        # Non-EU
        {
            "title": "Export of Goods - Zero Rated",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Export Outside EU",
                "rate": 0
            }]
        },
        {
            "title": "Export of Services - Zero Rated",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Services to Non-EU Customers",
                "rate": 0
            }]
        },
        
        # Special cases
        {
            "title": "Triangulation Sales",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("VAT Control", company),
                "description": "VAT 0% - Triangulation",
                "rate": 0
            }]
        },
        {
            "title": "Margin Scheme Sales",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account("Cyprus Standard Rate VAT Output (19%)", company),
                "description": "VAT 19% on Margin",
                "add_deduct_tax": "Add",
                "rate": 19
            }]
        }
    ]
    
    # Create EU B2C Digital Services templates for each country
    for country, country_data in eu_country_rates.items():
        rate = country_data["rate"]
        code = country_data["code"]
        
        # Digital services template
        templates.append({
            "title": f"EU B2C Digital Services - {country}",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account(f"VAT OSS {code} ({country})", company),
                "description": f"{country} VAT {rate}% - OSS Digital Services",
                "add_deduct_tax": "Add",
                "rate": rate
            }]
        })
        
        # Goods template for OSS
        templates.append({
            "title": f"EU B2C Goods - {country}",
            "taxes": [{
                "charge_type": "On Net Total",
                "account_head": find_account(f"VAT OSS {code} ({country})", company),
                "description": f"{country} VAT {rate}% - OSS Goods",
                "add_deduct_tax": "Add",
                "rate": rate
            }]
        })
    
    # Create the tax templates
    created_count = 0
    for template in templates:
        if create_sales_tax_template(company, template):
            created_count += 1
    
    if created_count > 0:
        return True
    else:
        return False

def create_sales_tax_template(company, template_data):
    """
    Create a single sales tax template if it doesn't already exist.
    
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
    
    if frappe.db.exists("Sales Taxes and Charges Template", template_name):
        return False
        
    # Create new template
    doc = frappe.new_doc("Sales Taxes and Charges Template")
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
        frappe.log_error(f"Error creating sales tax template {title}: {str(e)}", "ERPNext Cyprus Setup Error")
        return False

def create_cyprus_tax_rules(company):
    """
    Create tax rules for Cyprus purchase tax templates.
    
    This method creates tax rules to automatically apply the appropriate purchase tax templates
    based on supplier country and item groups.
    
    Args:
        company (str): The company name
        
    Returns:
        bool: True if tax rules were created, False otherwise
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Check if company is in Cyprus
    if frappe.db.get_value("Company", company, "country") != "Cyprus":
        return False
    
    # Get EU country codes
    eu_countries = [
        "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", 
        "Czech Republic", "Denmark", "Estonia", "Finland", "France", 
        "Germany", "Greece", "Hungary", "Ireland", "Italy", 
        "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", 
        "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", 
        "Spain", "Sweden"
    ]
    
    # Define the tax rules
    tax_rules = [
        # EU Digital Services Rule - Highest priority
        {
            "title": "EU Digital Services Purchase",
            "tax_type": "Purchase",
            "priority": 1,
            "use_for_shopping_cart": 0,
            "item_group": "Digital Services",
            "billing_country": None,  # Will be set in loop for each EU country
            "billing_city": "",
            "tax_template": f"EU Digital Services - Reverse Charge - {company_abbr}",
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # Non-EU Digital Services Rule
        {
            "title": "Non-EU Digital Services Purchase",
            "tax_type": "Purchase",
            "priority": 2,
            "use_for_shopping_cart": 0,
            "item_group": "Digital Services",
            "billing_country": "",  # Any non-EU country
            "billing_city": "",
            "tax_template": f"Non-EU Digital Services - Reverse Charge - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        },
        
        # EU Goods Purchase Rule
        {
            "title": "EU Goods Purchase",
            "tax_type": "Purchase",
            "priority": 3,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item group except Digital Services
            "billing_country": None,  # Will be set in loop for each EU country
            "billing_city": "",
            "tax_template": f"EU Purchase - Goods - Reverse Charge - {company_abbr}",
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # EU Services Purchase Rule
        {
            "title": "EU Services Purchase",
            "tax_type": "Purchase",
            "priority": 4,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item group except Digital Services
            "billing_country": None,  # Will be set in loop for each EU country
            "billing_city": "",
            "tax_template": f"EU Purchase - Services - Reverse Charge - {company_abbr}",
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # Import with VAT Rule
        {
            "title": "Import with VAT",
            "tax_type": "Purchase",
            "priority": 5,
            "use_for_shopping_cart": 0,
            "item_group": "",
            "billing_country": "",  # Any non-EU country
            "billing_city": "",
            "tax_template": f"Import with VAT - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        },
        
        # Default Cyprus VAT Rule - Lowest priority (fallback)
        {
            "title": "Cyprus Standard Purchase VAT",
            "tax_type": "Purchase",
            "priority": 50,
            "use_for_shopping_cart": 0,
            "item_group": "",
            "billing_country": "Cyprus",
            "billing_city": "",
            "tax_template": f"Cyprus Purchase VAT 19% - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        }
    ]
    
    # Create tax rules
    created_count = 0
    
    # First, create non-EU country rules (these don't need country-specific versions)
    non_eu_rules = [rule for rule in tax_rules if not rule.get("is_eu")]
    for rule in non_eu_rules:
        if create_tax_rule(company, rule):
            created_count += 1
    
    # Then create EU country-specific rules
    eu_rules = [rule for rule in tax_rules if rule.get("is_eu")]
    for rule in eu_rules:
        base_title = rule["title"]
        for country in eu_countries:
            if country != "Cyprus":  # Skip Cyprus, as it's handled by domestic rules
                country_rule = rule.copy()
                country_rule["title"] = f"{base_title} - {country}"
                country_rule["billing_country"] = country
                if create_tax_rule(company, country_rule):
                    created_count += 1
    
    if created_count > 0:
        return True
    else:
        return False

def create_tax_rule(company, rule_data):
    """
    Create a single tax rule if it doesn't already exist.
    
    Args:
        company (str): The company name
        rule_data (dict): Rule data with tax_type, and other filter criteria
    
    Returns:
        bool: True if created, False if already exists
    """
    # Check if rule already exists - using the appropriate filters
    filters = {
        "tax_type": rule_data["tax_type"],
        "company": company
    }
    
    # Add specific filters used in this rule
    if rule_data.get("item_group"):
        filters["item_group"] = rule_data["item_group"]
    
    if rule_data.get("billing_country"):
        filters["billing_country"] = rule_data["billing_country"]
    
    if rule_data.get("shipping_country"):
        filters["shipping_country"] = rule_data["shipping_country"]
    
    if rule_data.get("supplier_group"):
        filters["supplier_group"] = rule_data["supplier_group"]
    
    # Check for tax template
    if rule_data["tax_type"] == "Purchase":
        filters["purchase_tax_template"] = rule_data["tax_template"]
    else:
        filters["sales_tax_template"] = rule_data["tax_template"]
    
    # Check if a rule with these criteria already exists
    existing_rules = frappe.db.get_all("Tax Rule", filters=filters)
    if existing_rules:
        return False
    
    # Create new rule
    tax_rule = frappe.new_doc("Tax Rule")
    tax_rule.tax_type = rule_data["tax_type"]
    tax_rule.company = company
    tax_rule.priority = rule_data.get("priority", 1)
    tax_rule.use_for_shopping_cart = rule_data.get("use_for_shopping_cart", 0)
    
    # Set filters
    if rule_data.get("item_group"):
        tax_rule.item_group = rule_data["item_group"]
    
    if rule_data.get("shipping_country"):
        tax_rule.shipping_country = rule_data["shipping_country"]
    
    if rule_data.get("shipping_city"):
        tax_rule.shipping_city = rule_data["shipping_city"]
    
    if rule_data.get("billing_country"):
        tax_rule.billing_country = rule_data["billing_country"]
    
    if rule_data.get("billing_city"):
        tax_rule.billing_city = rule_data["billing_city"]
    
    if rule_data.get("supplier_group"):
        tax_rule.supplier_group = rule_data["supplier_group"]
    
    # Set the tax template
    if rule_data["tax_type"] == "Purchase":
        tax_rule.purchase_tax_template = rule_data["tax_template"]
    else:
        tax_rule.sales_tax_template = rule_data["tax_template"]
    
    # Set validity period if specified
    if rule_data.get("from_date"):
        tax_rule.from_date = rule_data["from_date"]
    
    if rule_data.get("to_date"):
        tax_rule.to_date = rule_data["to_date"]
    
    try:
        tax_rule.save()
        return True
    except Exception as e:
        frappe.log_error(f"Error creating tax rule: {str(e)}", "ERPNext Cyprus Setup Error")
        return False

def create_cyprus_sales_tax_rules(company):
    """
    Create tax rules for Cyprus sales tax templates.
    
    This method creates tax rules to automatically apply the appropriate sales tax templates
    based on customer country, item groups, and B2B/B2C status via customer groups.
    
    Args:
        company (str): The company name
        
    Returns:
        bool: True if tax rules were created, False otherwise
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Check if company is in Cyprus
    if frappe.db.get_value("Company", company, "country") != "Cyprus":
        return False
    
    # Get EU country codes
    eu_countries = [
        "Austria", "Belgium", "Bulgaria", "Croatia", 
        "Czech Republic", "Denmark", "Estonia", "Finland", "France", 
        "Germany", "Greece", "Hungary", "Ireland", "Italy", 
        "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", 
        "Poland", "Portugal", "Romania", "Slovakia", "Slovenia", 
        "Spain", "Sweden"
    ]
    
    # Define the base tax rules for sales
    tax_rules = [
        # Digital Services Rules - Country specific - Highest priority
        {
            "title": "EU B2C Digital Services",
            "tax_type": "Sales",
            "priority": 1,
            "use_for_shopping_cart": 1,
            "item_group": "Digital Services",
            "customer_group": "Individual",  # B2C customers
            "shipping_country": None,  # Will be set in loop for each EU country
            "shipping_city": "",
            "tax_template": None,  # Will be set in loop for each country
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # EU B2C Goods OSS Rules - Country specific
        {
            "title": "EU B2C Goods OSS",
            "tax_type": "Sales",
            "priority": 2,
            "use_for_shopping_cart": 1,
            "item_group": "",  # Any item
            "customer_group": "Individual",  # B2C customers
            "shipping_country": None,  # Will be set in loop for each EU country
            "shipping_city": "",
            "tax_template": None,  # Will be set in loop for each country
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # EU B2B Goods Rule - Same for all EU countries
        {
            "title": "EU B2B Goods Sales",
            "tax_type": "Sales",
            "priority": 3,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item
            "customer_group": "Commercial",  # B2B customers
            "shipping_country": None,  # Will be set in loop for each EU country
            "shipping_city": "",
            "tax_template": f"EU B2B Goods - Zero Rated - {company_abbr}",
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # EU B2B Services Rule - Same for all EU countries
        {
            "title": "EU B2B Services Sales",
            "tax_type": "Sales",
            "priority": 4,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item
            "customer_group": "Commercial",  # B2B customers
            "shipping_country": None,  # Will be set in loop for each EU country
            "shipping_city": "",
            "tax_template": f"EU B2B Services - Zero Rated - {company_abbr}",
            "is_eu": True,
            "from_date": None,
            "to_date": None
        },
        
        # Export of Goods - Zero Rated (Non-EU)
        {
            "title": "Export of Goods - Zero Rated",
            "tax_type": "Sales",
            "priority": 5,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item
            "shipping_country": "",  # Any non-EU, non-Cyprus country
            "shipping_city": "",
            "tax_template": f"Export of Goods - Zero Rated - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        },
        
        # Export of Services - Zero Rated (Non-EU)
        {
            "title": "Export of Services - Zero Rated",
            "tax_type": "Sales",
            "priority": 6,
            "use_for_shopping_cart": 0,
            "item_group": "",  # Any item
            "shipping_country": "",  # Any non-EU, non-Cyprus country
            "shipping_city": "",
            "tax_template": f"Export of Services - Zero Rated - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        },
        
        # Default Cyprus VAT Rule - Lowest priority (fallback)
        {
            "title": "Cyprus Standard VAT Sales",
            "tax_type": "Sales",
            "priority": 50,
            "use_for_shopping_cart": 0,
            "item_group": "",
            "shipping_country": "Cyprus",
            "shipping_city": "",
            "tax_template": f"Cyprus Sales VAT 19% - {company_abbr}",
            "is_eu": False,
            "from_date": None,
            "to_date": None
        }
    ]
    
    # Create tax rules
    created_count = 0
    
    # First, create country-specific rules for EU B2C Digital Services and Goods
    eu_specific_rules = [rule for rule in tax_rules if rule.get("is_eu") and rule["tax_template"] is None]
    for rule in eu_specific_rules:
        base_title = rule["title"]
        for country in eu_countries:
            if country != "Cyprus":  # Skip Cyprus, as it's handled by domestic rules
                country_rule = rule.copy()
                country_rule["title"] = f"{base_title} - {country}"
                country_rule["shipping_country"] = country
                
                # Set the appropriate tax template based on rule type and country
                if "Digital Services" in base_title:
                    country_rule["tax_template"] = f"EU B2C Digital Services - {country} - {company_abbr}"
                elif "Goods OSS" in base_title:
                    country_rule["tax_template"] = f"EU B2C Goods - {country} - {company_abbr}"
                
                if create_sales_tax_rule(company, country_rule):
                    created_count += 1
    
    # Then create EU country-general rules (B2B goods and services)
    eu_general_rules = [rule for rule in tax_rules if rule.get("is_eu") and rule["tax_template"] is not None]
    for rule in eu_general_rules:
        base_title = rule["title"]
        for country in eu_countries:
            if country != "Cyprus":  # Skip Cyprus, as it's handled by domestic rules
                country_rule = rule.copy()
                country_rule["title"] = f"{base_title} - {country}"
                country_rule["shipping_country"] = country
                if create_sales_tax_rule(company, country_rule):
                    created_count += 1
    
    # Finally, create non-EU and Cyprus rules
    non_eu_rules = [rule for rule in tax_rules if not rule.get("is_eu")]
    for rule in non_eu_rules:
        if create_sales_tax_rule(company, rule):
            created_count += 1
    
    if created_count > 0:
        return True
    else:
        return False

def create_sales_tax_rule(company, rule_data):
    """
    Create a single sales tax rule if it doesn't already exist.
    
    Args:
        company (str): The company name
        rule_data (dict): Rule data with tax_type, and other filter criteria
    
    Returns:
        bool: True if created, False if already exists
    """
    # Check if rule already exists - using the appropriate filters
    filters = {
        "tax_type": rule_data["tax_type"],
        "company": company
    }
    
    # Add specific filters used in this rule
    if rule_data.get("item_group"):
        filters["item_group"] = rule_data["item_group"]
    
    if rule_data.get("customer_group"):
        filters["customer_group"] = rule_data["customer_group"]
    
    if rule_data.get("shipping_country"):
        filters["shipping_country"] = rule_data["shipping_country"]
    
    if rule_data.get("billing_country"):
        filters["billing_country"] = rule_data["billing_country"]
    
    if rule_data.get("supplier_group"):
        filters["supplier_group"] = rule_data["supplier_group"]
    
    # Check for tax template
    if rule_data["tax_type"] == "Sales":
        filters["sales_tax_template"] = rule_data["tax_template"]
    else:
        filters["purchase_tax_template"] = rule_data["tax_template"]
    
    # Check if a rule with these criteria already exists
    existing_rules = frappe.db.get_all("Tax Rule", filters=filters)
    if existing_rules:
        return False
    
    # Create new rule
    tax_rule = frappe.new_doc("Tax Rule")
    tax_rule.tax_type = rule_data["tax_type"]
    tax_rule.company = company
    tax_rule.priority = rule_data.get("priority", 1)
    tax_rule.use_for_shopping_cart = rule_data.get("use_for_shopping_cart", 0)
    
    # Set filters
    if rule_data.get("item_group"):
        tax_rule.item_group = rule_data["item_group"]
    
    if rule_data.get("customer_group"):
        tax_rule.customer_group = rule_data["customer_group"]
    
    if rule_data.get("shipping_country"):
        tax_rule.shipping_country = rule_data["shipping_country"]
    
    if rule_data.get("shipping_city"):
        tax_rule.shipping_city = rule_data["shipping_city"]
    
    if rule_data.get("billing_country"):
        tax_rule.billing_country = rule_data["billing_country"]
    
    if rule_data.get("billing_city"):
        tax_rule.billing_city = rule_data["billing_city"]
    
    if rule_data.get("supplier_group"):
        tax_rule.supplier_group = rule_data["supplier_group"]
    
    # Set the tax template
    if rule_data["tax_type"] == "Sales":
        tax_rule.sales_tax_template = rule_data["tax_template"]
    else:
        tax_rule.purchase_tax_template = rule_data["tax_template"]
    
    # Set validity period if specified
    if rule_data.get("from_date"):
        tax_rule.from_date = rule_data["from_date"]
    
    if rule_data.get("to_date"):
        tax_rule.to_date = rule_data["to_date"]
    
    try:
        tax_rule.save()
        return True
    except Exception as e:
        frappe.log_error(f"Error creating sales tax rule: {str(e)}", "ERPNext Cyprus Setup Error")
        return False
