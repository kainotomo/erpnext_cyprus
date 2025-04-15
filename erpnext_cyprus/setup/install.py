import frappe
from frappe import _
import os
import json
import shutil

def after_install():
    """Run after installation"""
    
    # Copy Cyprus Chart of Accounts
    copy_chart_of_accounts()

    # Ensure customer groups exist
    ensure_customer_groups()

    # Ensure item groups exist
    ensure_item_groups()

def copy_chart_of_accounts():
    """Add Cyprus Chart of Accounts"""
    
    # Add chart of accounts files to the expected location
    charts_path = frappe.get_app_path("erpnext", "accounts", "doctype", "account", "chart_of_accounts", "verified")
    
    # Define source and target paths for both chart templates
    templates = [
        {
            "source": frappe.get_app_path("erpnext_cyprus", "setup", "chart_of_accounts", "cyprus_chart_template.json"),
            "target": os.path.join(charts_path, "cy_cyprus_chart_template.json"),
            "name": "Cyprus Standard"
        },
        {
            "source": frappe.get_app_path("erpnext_cyprus", "setup", "chart_of_accounts", "cyprus_chart_template_numbered.json"),
            "target": os.path.join(charts_path, "cy_cyprus_chart_template_numbered.json"),
            "name": "Cyprus Standard Numbered"
        }
    ]
    
    # Copy each template to ERPNext's verified folder
    for template in templates:
        if os.path.exists(template["source"]):
            try:
                # Create a backup if the file already exists
                if os.path.exists(template["target"]):
                    backup_path = template["target"] + ".bak"
                    shutil.copy2(template["target"], backup_path)
                
                # Copy the template
                with open(template["source"], 'r') as source_file:
                    chart_data = json.load(source_file)
                
                with open(template["target"], 'w') as target_file:
                    json.dump(chart_data, target_file, indent=4)
                    
                frappe.log_error(f"{template['name']} chart template installed successfully", "ERPNext Cyprus Install")
                
            except Exception as e:
                frappe.log_error(f"Error installing {template['name']} chart template: {str(e)}", "ERPNext Cyprus Install Error")
        else:
            frappe.log_error(f"Source template file not found: {template['source']}", "ERPNext Cyprus Install Error")
    
    frappe.msgprint(_("Cyprus Chart of Accounts templates have been installed."))

def ensure_customer_groups():
    """Create 'Commercial' and 'Individual' customer groups if they don't exist."""
    for group in ["Commercial", "Individual"]:
        if not frappe.db.exists("Customer Group", {"customer_group_name": group}):
            doc = frappe.new_doc("Customer Group")
            doc.customer_group_name = group
            doc.parent_customer_group = "All Customer Groups"
            doc.is_group = 0
            doc.save(ignore_permissions=True)

def ensure_item_groups():
    # Ensure Digital Services item group exists
    digital_services_group = "Digital Services"
    if not frappe.db.exists("Item Group", {"item_group_name": digital_services_group}):
        ig_doc = frappe.new_doc("Item Group")
        ig_doc.item_group_name = digital_services_group
        ig_doc.is_group = 0
        ig_doc.insert(ignore_permissions=True)

def create_cyprus_tax_templates(company):
    """Create Cyprus tax templates for the specified company"""
    try:
        company_abbr = frappe.get_cached_value("Company", company, "abbr")
        
        # First, ensure required parent accounts exist
        ensure_parent_accounts_exist(company)
        
        # Define VAT accounts with account details
        vat_accounts = {
            # Output VAT accounts (now under Tax Liabilities)
            "standard_output": {
                "name": f"Cyprus Standard Rate VAT Output (19%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "tax_rate": 19
            },
            "reduced_output_9": {
                "name": f"Cyprus Reduced Rate VAT Output (9%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "tax_rate": 9
            },
            "reduced_output_5": {
                "name": f"Cyprus Reduced Rate VAT Output (5%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "tax_rate": 5
            },
            "eu_reverse_output": {
                "name": f"EU Reverse Charge VAT Output - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "tax_rate": 19
            },
            "self_supply_output": {
                "name": f"Self-Supply VAT Output - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "tax_rate": 19
            },
            # Input VAT accounts (under Current Assets)
            "standard_input": {
                "name": f"Cyprus Standard Rate VAT Input (19%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "tax_rate": 19
            },
            "reduced_input_9": {
                "name": f"Cyprus Reduced Rate VAT Input (9%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "tax_rate": 9
            },
            "reduced_input_5": {
                "name": f"Cyprus Reduced Rate VAT Input (5%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "tax_rate": 5
            },
            "eu_input": {
                "name": f"EU Acquisition VAT Input - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "tax_rate": 19
            },
            "import_input": {
                "name": f"Import VAT Input - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "tax_rate": 19
            },
            "non_deductible_vat": {
                "name": f"Non-Deductible VAT - {company_abbr}",
                "parent": "Tax Expense",
                "is_group": 0,
                "tax_rate": 19
            },
            # Control accounts
            "vat_control": {
                "name": f"VAT Control - {company_abbr}",
                "parent": "Tax Liabilities",
                "is_group": 0
            },
            "vat_payable": {
                "name": f"VAT Payable - {company_abbr}",
                "parent": "Tax Liabilities",
                "is_group": 0
            },
            # OSS Accounts (all EU member states except Cyprus)
            "oss_at": {"name": f"VAT OSS AT (Austria) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 20},
            "oss_be": {"name": f"VAT OSS BE (Belgium) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_bg": {"name": f"VAT OSS BG (Bulgaria) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 20},
            "oss_hr": {"name": f"VAT OSS HR (Croatia) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 25},
            "oss_cz": {"name": f"VAT OSS CZ (Czech Republic) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_dk": {"name": f"VAT OSS DK (Denmark) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 25},
            "oss_ee": {"name": f"VAT OSS EE (Estonia) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 20},
            "oss_fi": {"name": f"VAT OSS FI (Finland) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 24},
            "oss_fr": {"name": f"VAT OSS FR (France) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 20},
            "oss_de": {"name": f"VAT OSS DE (Germany) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 19},
            "oss_gr": {"name": f"VAT OSS GR (Greece) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 24},
            "oss_hu": {"name": f"VAT OSS HU (Hungary) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 27},
            "oss_ie": {"name": f"VAT OSS IE (Ireland) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 23},
            "oss_it": {"name": f"VAT OSS IT (Italy) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 22},
            "oss_lv": {"name": f"VAT OSS LV (Latvia) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_lt": {"name": f"VAT OSS LT (Lithuania) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_lu": {"name": f"VAT OSS LU (Luxembourg) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 17},
            "oss_mt": {"name": f"VAT OSS MT (Malta) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 18},
            "oss_nl": {"name": f"VAT OSS NL (Netherlands) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_pl": {"name": f"VAT OSS PL (Poland) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 23},
            "oss_pt": {"name": f"VAT OSS PT (Portugal) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 23},
            "oss_ro": {"name": f"VAT OSS RO (Romania) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 19},
            "oss_sk": {"name": f"VAT OSS SK (Slovakia) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 20},
            "oss_si": {"name": f"VAT OSS SI (Slovenia) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 22},
            "oss_es": {"name": f"VAT OSS ES (Spain) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 21},
            "oss_se": {"name": f"VAT OSS SE (Sweden) - {company_abbr}", "parent": "VAT OSS", "is_group": 0, "tax_rate": 25}
        }
        
        # Verify and create VAT accounts if they don't exist
        accounts = {}
        for key, account_data in vat_accounts.items():
            account_name = account_data["name"]
            accounts[key] = account_name
            
            # Check if account exists
            if not frappe.db.exists("Account", {"name": account_name, "company": company}):
                # Try to find the parent account
                parent_account = find_parent_account(account_data["parent"], company)
                if not parent_account:
                    frappe.msgprint(f"Could not find parent account '{account_data['parent']}' for {account_name}. Using temporary parent.")
                    if "Input" in account_name:
                        parent_account = f"Current Assets - {company_abbr}"
                    elif "Output" in account_name or "OSS" in account_name or "Control" in account_name or "Payable" in account_name:
                        parent_account = f"Current Liabilities - {company_abbr}"
                    else:
                        parent_account = f"Expenses - {company_abbr}"
                
                # Create the account
                create_account(
                    account_name=account_name,
                    company=company,
                    parent_account=parent_account,
                    is_group=account_data["is_group"],
                    account_type=None
                )
                frappe.msgprint(f"Created account: {account_name}")
        
        # Create Sales tax templates
        sales_templates = [
            {
                "title": "Cyprus VAT 19%",
                "is_default": 1,
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["standard_output"],
                    "description": "VAT 19%",
                    "rate": 19
                }]
            },
            {
                "title": "Cyprus VAT 9%",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["reduced_output_9"],
                    "description": "VAT 9%",
                    "rate": 9
                }]
            },
            {
                "title": "Cyprus VAT 5%",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["reduced_output_5"],
                    "description": "VAT 5%",
                    "rate": 5
                }]
            },
            {
                "title": "Cyprus VAT 0% (Zero Rated)",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Zero Rate",
                    "rate": 0
                }]
            },
            {
                "title": "Cyprus VAT Exempt",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT Exempt",
                    "rate": 0
                }]
            },
            {
                "title": "EU B2B Sales - Goods - Reverse Charge",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Reverse Charge - Art. 138 EU VAT Directive",
                    "rate": 0
                }]
            },
            {
                "title": "EU B2B Sales - Services - Reverse Charge",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Reverse Charge - Art. 44 EU VAT Directive",
                    "rate": 0
                }]
            },
            {
                "title": "Non-EU Exports - Zero Rated",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Export Outside EU",
                    "rate": 0
                }]
            },
            {
                "title": "Self-Supply VAT",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["self_supply_output"],
                    "description": "Self-Supply VAT 19%",
                    "rate": 19
                }]
            }
        ]
        
        # Add OSS tax templates for all EU member states except Cyprus
        oss_templates = []
        
        # OSS Tax Templates - Digital Services
        for country_code in ["AT", "BE", "BG", "HR", "CZ", "DK", "EE", "FI", 
                             "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", 
                             "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]:
            country_key = f"oss_{country_code.lower()}"
            if country_key in accounts:
                country_name = get_country_name(country_code)
                tax_rate = vat_accounts[country_key]["tax_rate"]
                
                # Template for digital services
                oss_templates.append({
                    "title": f"EU B2C Sales - Digital Services - {country_code}",
                    "taxes": [{
                        "charge_type": "On Net Total",
                        "account_head": accounts[country_key],
                        "description": f"{country_code} VAT {tax_rate}% - OSS Digital",
                        "rate": tax_rate
                    }]
                })
                
                # Template for goods
                oss_templates.append({
                    "title": f"EU B2C Sales - Goods - {country_code}",
                    "taxes": [{
                        "charge_type": "On Net Total",
                        "account_head": accounts[country_key],
                        "description": f"{country_code} VAT {tax_rate}% - OSS Goods",
                        "rate": tax_rate
                    }]
                })
        
        # Add OSS templates to sales templates
        sales_templates.extend(oss_templates)
        
        # Create Purchase tax templates
        purchase_templates = [
            {
                "title": "Cyprus Purchase VAT 19%",
                "is_default": 1,
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["standard_input"],
                    "description": "VAT 19%",
                    "add_deduct_tax": "Add",
                    "rate": 19
                }]
            },
            {
                "title": "Cyprus Purchase VAT 9%",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["reduced_input_9"],
                    "description": "VAT 9%",
                    "add_deduct_tax": "Add",
                    "rate": 9
                }]
            },
            {
                "title": "Cyprus Purchase VAT 5%",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["reduced_input_5"],
                    "description": "VAT 5%",
                    "add_deduct_tax": "Add",
                    "rate": 5
                }]
            },
            {
                "title": "Cyprus Purchase VAT 0% (Zero Rated)",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Zero Rate",
                    "rate": 0
                }]
            },
            {
                "title": "Cyprus Purchase VAT Exempt",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["vat_control"],
                    "description": "VAT Exempt",
                    "rate": 0
                }]
            },
            {
                "title": "EU Purchase - Goods - Reverse Charge",
                "taxes": [
                    {
                        "charge_type": "On Net Total",
                        "account_head": accounts["eu_reverse_output"],
                        "description": "VAT 19% - Reverse Charge Output",
                        "add_deduct_tax": "Add",
                        "rate": 19
                    },
                    {
                        "charge_type": "On Net Total",
                        "account_head": accounts["eu_input"],
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
                        "account_head": accounts["eu_reverse_output"],
                        "description": "VAT 19% - Reverse Charge Output",
                        "add_deduct_tax": "Add",
                        "rate": 19
                    },
                    {
                        "charge_type": "On Net Total",
                        "account_head": accounts["eu_input"],
                        "description": "VAT 19% - Reverse Charge Input",
                        "add_deduct_tax": "Deduct",
                        "rate": 19
                    }
                ]
            },
            {
                "title": "Import with VAT",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["import_input"],
                    "description": "Import VAT 19%",
                    "add_deduct_tax": "Add",
                    "rate": 19
                }]
            },
            {
                "title": "Purchase with Non-Deductible VAT",
                "taxes": [{
                    "charge_type": "On Net Total",
                    "account_head": accounts["non_deductible_vat"],
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
                        "account_head": accounts["standard_input"],
                        "description": "Deductible VAT 19% (50%)",
                        "add_deduct_tax": "Add",
                        "rate": 9.5
                    },
                    {
                        "charge_type": "On Net Total",
                        "account_head": accounts["non_deductible_vat"],
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
                    "account_head": accounts["vat_control"],
                    "description": "VAT 0% - Triangulation",
                    "rate": 0
                }]
            }
        ]
        
        # Create sales tax templates
        for template in sales_templates:
            create_tax_template(template, company, "Sales Taxes and Charges Template")
            
        # Create purchase tax templates
        for template in purchase_templates:
            create_tax_template(template, company, "Purchase Taxes and Charges Template")
        
        # After creating all tax templates
        frappe.db.commit()  # Ensure all templates are saved to the DB

        # Now create tax rules
        create_cyprus_tax_rules(company)
        
        frappe.msgprint(_("Cyprus tax templates have been created for company {0}.").format(company))
        
        # Log successful creation
        frappe.log_error(f"Cyprus tax templates created for company {company}", "ERPNext Cyprus Setup")
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error creating Cyprus tax templates for {company}: {str(e)}", "ERPNext Cyprus Setup Error")
        return False

def create_cyprus_tax_rules(company):
    """
    Create Tax Rules for all Cyprus VAT scenarios for the given company, including all OSS countries.
    """
    
    # --- Cyprus VAT rates (Sales & Purchase, B2B & B2C) ---
    cy_vat_rates = [
        ("Cyprus VAT 19%", "Cyprus Purchase VAT 19%"),
        ("Cyprus VAT 9%", "Cyprus Purchase VAT 9%"),
        ("Cyprus VAT 5%", "Cyprus Purchase VAT 5%"),
        ("Cyprus VAT 0% (Zero Rated)", "Cyprus Purchase VAT 0% (Zero Rated)"),
        ("Cyprus VAT Exempt", "Cyprus Purchase VAT Exempt"),
    ]
    for sales_tpl, purchase_tpl in cy_vat_rates:
        # Sales B2C
        create_tax_rule(
            company=company,
            party_type="Customer",
            country="Cyprus",
            customer_group="Individual",
            tax_template=sales_tpl,
            tax_type="Sales"
        )
        # Sales B2B
        create_tax_rule(
            company=company,
            party_type="Customer",
            country="Cyprus",
            customer_group="Commercial",
            tax_template=sales_tpl,
            tax_type="Sales"
        )
        # Purchase (all suppliers)
        create_tax_rule(
            company=company,
            party_type="Supplier",
            country="Cyprus",
            tax_template=purchase_tpl,
            tax_type="Purchase"
        )

    # --- EU B2B Sales (Reverse Charge) for all EU except Cyprus ---
    oss_countries = [
        ("AT", "Austria", 20), ("BE", "Belgium", 21), ("BG", "Bulgaria", 20), ("HR", "Croatia", 25),
        ("CZ", "Czech Republic", 21), ("DK", "Denmark", 25), ("EE", "Estonia", 20), ("FI", "Finland", 24),
        ("FR", "France", 20), ("DE", "Germany", 19), ("GR", "Greece", 24), ("HU", "Hungary", 27),
        ("IE", "Ireland", 23), ("IT", "Italy", 22), ("LV", "Latvia", 21), ("LT", "Lithuania", 21),
        ("LU", "Luxembourg", 17), ("MT", "Malta", 18), ("NL", "Netherlands", 21), ("PL", "Poland", 23),
        ("PT", "Portugal", 23), ("RO", "Romania", 19), ("SK", "Slovakia", 20), ("SI", "Slovenia", 22),
        ("ES", "Spain", 21), ("SE", "Sweden", 25)
    ]
    for code, country, rate in oss_countries:
        # EU B2B Goods
        create_tax_rule(
            company=company,
            party_type="Customer",
            country=country,
            customer_group="Commercial",
            tax_template="EU B2B Sales - Goods - Reverse Charge",
            tax_type="Sales"
        )
        # EU B2B Services
        create_tax_rule(
            company=company,
            party_type="Customer",
            country=country,
            customer_group="Commercial",
            tax_template="EU B2B Sales - Services - Reverse Charge",
            tax_type="Sales"
        )
        # OSS Goods (B2C)
        create_tax_rule(
            company=company,
            party_type="Customer",
            country=country,
            customer_group="Individual",
            tax_template=f"EU B2C Sales - Goods - {code}",
            tax_type="Sales"
        )
        # OSS Digital Services (B2C, with item group)
        create_tax_rule(
            company=company,
            party_type="Customer",
            country=country,
            customer_group="Individual",
            tax_template=f"EU B2C Sales - Digital Services - {code}",
            tax_type="Sales",
            item_group=digital_services_group
        )

    # --- Non-EU Sale (USA) ---
    create_tax_rule(
        company=company,
        party_type="Customer",
        country="United States",
        tax_template="Non-EU Exports - Zero Rated",
        tax_type="Sales"
    )

    # --- Purchase: EU, Non-EU, and Special Cases ---
    # EU Purchase (all EU except Cyprus)
    for code, country, rate in oss_countries:
        create_tax_rule(
            company=company,
            party_type="Supplier",
            country=country,
            tax_template="EU Purchase - Goods - Reverse Charge",
            tax_type="Purchase"
        )
        create_tax_rule(
            company=company,
            party_type="Supplier",
            country=country,
            tax_template="EU Purchase - Services - Reverse Charge",
            tax_type="Purchase"
        )

    # Non-EU Purchase (USA)
    create_tax_rule(
        company=company,
        party_type="Supplier",
        country="United States",
        tax_template="Import with VAT",
        tax_type="Purchase"
    )

    # Special Purchase Cases (applies to Cyprus)
    special_purchase_templates = [
        "Purchase with Non-Deductible VAT",
        "Purchase with Partial VAT Deduction (50%)",
        "Purchase - Triangulation"
    ]
    for tpl in special_purchase_templates:
        create_tax_rule(
            company=company,
            party_type="Supplier",
            country="Cyprus",
            tax_template=tpl,
            tax_type="Purchase"
        )

def create_tax_rule(company, party_type, country, tax_template, tax_type, customer_group=None, item_group=None):
    """
    Create a Tax Rule if it does not already exist, using the correct field for sales or purchase tax template.
    """
    # Get company abbreviation
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    # Construct the correct template name as used in ERPNext (Title - Company Abbreviation)
    template_name = f"{tax_template} - {company_abbr}"
    filters = {
        "company": company,
        "party_type": party_type,
        "tax_type": tax_type
    }
    # Use billing_country for country filter
    if country:
        filters["billing_country"] = country
    if customer_group:
        filters["customer_group"] = customer_group
    if item_group:
        filters["item_group"] = item_group
    # Determine the correct template field
    if tax_type == "Sales":
        filters["sales_tax_template"] = template_name
    elif tax_type == "Purchase":
        filters["purchase_tax_template"] = template_name
    doctype = "Tax Rule"
    if not frappe.db.exists(doctype, filters):
        doc = frappe.new_doc(doctype)
        doc.company = company
        doc.party_type = party_type
        doc.tax_type = tax_type
        if country:
            doc.billing_country = country
        if tax_type == "Sales":
            doc.sales_tax_template = template_name
        elif tax_type == "Purchase":
            doc.purchase_tax_template = template_name
        if customer_group:
            doc.customer_group = customer_group
        if item_group:
            doc.item_group = item_group
        doc.save(ignore_permissions=True)

def ensure_parent_accounts_exist(company):
    """
    Ensure that the necessary parent accounts exist for Cyprus VAT setup
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Define the parent accounts structure
    parent_accounts = {
        # VAT Input under Current Assets
        "VAT Input": {
            "name": f"VAT Input - {company_abbr}",
            "parent": f"Tax - {company_abbr}",
            "is_group": 1,
            "account_type": "Tax",
            "root_type": "Asset"
        },
        # VAT output and OSS under Current Liabilities > Tax Liabilities
        "Tax Liabilities": {
            "name": f"Tax Liabilities - {company_abbr}",
            "parent": f"Current Liabilities - {company_abbr}",
            "is_group": 1,
            "account_type": "Tax",
            "root_type": "Liability"
        },
        "VAT Output": {
            "name": f"VAT Output - {company_abbr}",
            "parent": f"Tax Liabilities - {company_abbr}",
            "is_group": 1,
            "account_type": "Tax",
            "root_type": "Liability"
        },
        "VAT OSS": {
            "name": f"VAT OSS - {company_abbr}",
            "parent": f"Tax Liabilities - {company_abbr}",
            "is_group": 1,
            "account_type": "Tax",
            "root_type": "Liability"
        },
        # Tax expense for Non-Deductible VAT
        "Tax Expense": {
            "name": f"Tax Expense - {company_abbr}",
            "parent": f"Expenses - {company_abbr}",
            "is_group": 1,
            "account_type": "Tax",
            "root_type": "Expense"
        }
    }
    
    # Make sure company root accounts exist
    ensure_root_accounts_exist(company)
    
    # Create parent accounts if they don't exist
    for _, account_data in parent_accounts.items():
        account_name = account_data["name"]
        
        # Check if account exists
        if not frappe.db.exists("Account", {"name": account_name, "company": company}):
            # Check if parent exists
            parent_account = account_data["parent"]
            if not frappe.db.exists("Account", {"name": parent_account, "company": company}):
                parent_parts = parent_account.split(" - ")
                if len(parent_parts) > 1:
                    parent_name = parent_parts[0].strip()
                    # Try to find the parent by name
                    parent_accounts = frappe.get_all(
                        "Account", 
                        filters={"account_name": parent_name, "company": company, "is_group": 1}
                    )
                    if parent_accounts:
                        parent_account = parent_accounts[0].name
                    else:
                        # If not found, use a root account based on root_type
                        if account_data["root_type"] == "Asset":
                            parent_account = f"Current Assets - {company_abbr}"
                        elif account_data["root_type"] == "Liability":
                            parent_account = f"Current Liabilities - {company_abbr}"
                        else:
                            parent_account = f"{account_data['root_type']}s - {company_abbr}"
            
            # Create the account
            try:
                create_account(
                    account_name=account_name,
                    company=company,
                    parent_account=parent_account,
                    is_group=account_data["is_group"],
                    account_type=account_data["account_type"] if account_data["account_type"] else None,
                    root_type=account_data["root_type"]
                )
                frappe.msgprint(f"Created parent account: {account_name}")
            except Exception as e:
                frappe.msgprint(f"Error creating account {account_name}: {str(e)}")

def ensure_root_accounts_exist(company):
    """
    Ensure that the root accounts for Cyprus VAT setup exist
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Define root accounts
    root_accounts = [
        {
            "account_name": "Current Assets",
            "name": f"Current Assets - {company_abbr}",
            "parent": f"Assets - {company_abbr}",
            "is_group": 1,
            "root_type": "Asset"
        },
        {
            "account_name": "Tax",
            "name": f"Tax - {company_abbr}",
            "parent": f"Current Assets - {company_abbr}",
            "is_group": 1,
            "root_type": "Asset"
        },
        {
            "account_name": "Current Liabilities",
            "name": f"Current Liabilities - {company_abbr}",
            "parent": f"Liabilities - {company_abbr}",
            "is_group": 1,
            "root_type": "Liability"
        },
        {
            "account_name": "Expenses",
            "name": f"Expenses - {company_abbr}",
            "parent": "",
            "is_group": 1,
            "root_type": "Expense"
        }
    ]
    
    # Create root accounts if they don't exist
    for account_data in root_accounts:
        account_name = account_data["name"]
        
        # Check if account exists
        if not frappe.db.exists("Account", {"name": account_name, "company": company}):
            try:
                # For Expenses, we need to check if the root account exists without abbreviation
                if account_data["account_name"] == "Expenses" and not account_data["parent"]:
                    parent_account = frappe.get_all(
                        "Account",
                        filters={"account_name": "Expenses", "company": company, "is_group": 1, "parent_account": ["is", "not set"]},
                        fields=["name"]
                    )
                    if parent_account:
                        continue
                
                # Create the account
                create_account(
                    account_name=account_data["account_name"],
                    company=company,
                    parent_account=account_data["parent"] if account_data["parent"] else None,
                    is_group=account_data["is_group"],
                    account_type="",
                    root_type=account_data["root_type"]
                )
                frappe.msgprint(f"Created root account: {account_name}")
            except Exception as e:
                frappe.msgprint(f"Error creating root account {account_name}: {str(e)}")

def create_account(account_name, company, parent_account, is_group=0, account_type=None, root_type=None):
    """
    Create an account with the given details
    """
    # If account_name includes company abbreviation, extract the actual account name
    if " - " in account_name:
        parts = account_name.split(" - ")
        account_name_only = " - ".join(parts[:-1])
    else:
        account_name_only = account_name
    
    # Create the account
    doc = frappe.new_doc("Account")
    doc.account_name = account_name_only
    doc.company = company
    doc.parent_account = parent_account
    doc.is_group = is_group
    
    if account_type:
        doc.account_type = account_type
    
    if root_type:
        doc.root_type = root_type
    
    try:
        doc.insert()
        return doc.name
    except frappe.DuplicateEntryError:
        # If the account already exists, return its name
        existing_account = frappe.get_all(
            "Account", 
            filters={
                "account_name": account_name_only, 
                "company": company,
                "parent_account": parent_account
            },
            fields=["name"]
        )
        if existing_account:
            return existing_account[0].name
        else:
            raise

def find_parent_account(parent_name, company):
    """
    Find a parent account by name in the company's chart of accounts
    """
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    potential_name = f"{parent_name} - {company_abbr}"
    
    # First try the exact match
    if frappe.db.exists("Account", {"name": potential_name, "company": company}):
        return potential_name
    
    # Next, try to find by account name
    parent_accounts = frappe.get_all(
        "Account", 
        filters={"account_name": parent_name, "company": company, "is_group": 1},
        fields=["name"]
    )
    
    if parent_accounts:
        return parent_accounts[0].name
    
    # Look for the parent account based on keywords
    account_map = {
        "VAT Input": ["Tax", "Current Assets"],
        "VAT Output": ["Tax Liabilities", "Current Liabilities"],
        "VAT OSS": ["Tax Liabilities", "Current Liabilities"],
        "Tax Liabilities": ["Current Liabilities"],
        "Tax Expense": ["Expenses"]
    }
    
    if parent_name in account_map:
        for keyword in account_map[parent_name]:
            keyword_accounts = frappe.get_all(
                "Account", 
                filters=[
                    ["account_name", "like", f"%{keyword}%"],
                    ["company", "=", company],
                    ["is_group", "=", 1]
                ],
                fields=["name"]
            )
            
            if keyword_accounts:
                return keyword_accounts[0].name
    
    return None

def create_tax_template(template_data, company, doctype):
    """
    Create a tax template for the company
    """
    title = template_data["title"]
    is_default = template_data.get("is_default", 0)
    taxes = template_data["taxes"]
    
    # Check if template already exists
    existing = frappe.get_all(
        doctype, 
        filters={
            "title": title,
            "company": company
        }
    )
    
    if existing:
        # Update existing template if needed
        doc = frappe.get_doc(doctype, existing[0].name)
        # Clear existing taxes
        doc.taxes = []
    else:
        # Create new template
        doc = frappe.new_doc(doctype)
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
        return doc.name
    except Exception as e:
        frappe.log_error(f"Error creating tax template {title}: {str(e)}", "ERPNext Cyprus Setup Error")
        return None

def get_country_name(country_code):
    """Get the full country name from country code"""
    country_names = {
        "AT": "Austria",
        "BE": "Belgium",
        "BG": "Bulgaria",
        "HR": "Croatia",
        "CY": "Cyprus",
        "CZ": "Czech Republic",
        "DK": "Denmark",
        "EE": "Estonia", 
        "FI": "Finland",
        "FR": "France",
        "DE": "Germany",
        "GR": "Greece",
        "HU": "Hungary",
        "IE": "Ireland",
        "IT": "Italy",
        "LV": "Latvia",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "MT": "Malta",
        "NL": "Netherlands",
        "PL": "Poland",
        "PT": "Portugal",
        "RO": "Romania",
        "SK": "Slovakia",
        "SI": "Slovenia",
        "ES": "Spain",
        "SE": "Sweden"
    }
    return country_names.get(country_code, country_code)