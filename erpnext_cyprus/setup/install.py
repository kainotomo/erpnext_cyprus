import frappe
from frappe import _
import os
import json
import shutil

def after_install():
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

@frappe.whitelist()
def setup_cyprus_tax_templates(company=None):
    """Setup Cyprus tax templates for the specified company"""
    if not company:
        companies = frappe.get_all("Company", filters={"country": "Cyprus"})
        for comp in companies:
            create_cyprus_tax_templates(comp.name)
        
        if companies:
            return {"status": "success", "message": "Cyprus tax templates created for all Cyprus companies"}
        else:
            return {"status": "error", "message": "No Cyprus companies found"}
    else:
        if frappe.db.get_value("Company", company, "country") == "Cyprus":
            create_cyprus_tax_templates(company)
            return {"status": "success", "message": f"Cyprus tax templates created for {company}"}
        else:
            return {"status": "error", "message": f"Company {company} is not set as a Cyprus company"}

def create_cyprus_tax_templates(company):
    """Create Cyprus tax templates for the specified company"""
    try:
        company_abbr = frappe.get_cached_value("Company", company, "abbr")
        
        # First, ensure required parent accounts exist
        ensure_parent_accounts_exist(company)
        
        # Define VAT accounts with account details
        vat_accounts = {
            # Output VAT accounts
            "standard_output": {
                "name": f"Cyprus Standard Rate VAT Output (19%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 19
            },
            "reduced_output_9": {
                "name": f"Cyprus Reduced Rate VAT Output (9%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 9
            },
            "reduced_output_5": {
                "name": f"Cyprus Reduced Rate VAT Output (5%) - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 5
            },
            "eu_reverse_output": {
                "name": f"EU Reverse Charge VAT Output - {company_abbr}",
                "parent": "VAT Output",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 19
            },
            # Input VAT accounts
            "standard_input": {
                "name": f"Cyprus Standard Rate VAT Input (19%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 19
            },
            "reduced_input_9": {
                "name": f"Cyprus Reduced Rate VAT Input (9%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 9
            },
            "reduced_input_5": {
                "name": f"Cyprus Reduced Rate VAT Input (5%) - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 5
            },
            "eu_input": {
                "name": f"EU Acquisition VAT Input - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 19
            },
            "import_input": {
                "name": f"Import VAT Input - {company_abbr}",
                "parent": "VAT Input",
                "is_group": 0,
                "account_type": "",
                "tax_rate": 19
            },
            # Control accounts
            "vat_control": {
                "name": f"VAT Control - {company_abbr}",
                "parent": "Tax",
                "is_group": 0,
                "account_type": ""
            }
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
                    parent_account = f"Current Assets - {company_abbr}"
                
                # Create the account
                create_account(
                    account_name=account_name,
                    company=company,
                    parent_account=parent_account,
                    is_group=account_data["is_group"],
                    account_type=account_data["account_type"] if account_data["account_type"] else None
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
                "title": "EU B2B Sales - Reverse Charge",
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
            }
        ]
        
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
                "title": "EU Purchase - Reverse Charge",
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
            }
        ]
        
        # Create sales tax templates
        for template in sales_templates:
            create_tax_template(template, company, "Sales Taxes and Charges Template")
            
        # Create purchase tax templates
        for template in purchase_templates:
            create_tax_template(template, company, "Purchase Taxes and Charges Template")
            
        frappe.msgprint(_("Cyprus tax templates have been created for company {0}.").format(company))
        
        # Log successful creation
        frappe.log_error(f"Cyprus tax templates created for company {company}", "ERPNext Cyprus Setup")
        
        return True
        
    except Exception as e:
        frappe.log_error(f"Error creating Cyprus tax templates for {company}: {str(e)}", "ERPNext Cyprus Setup Error")
        return False

def ensure_parent_accounts_exist(company):
    """Ensure that required parent accounts for VAT exist"""
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # First ensure the base structure exists
    check_base_chart_accounts(company)
    
    # Define VAT-specific parent accounts
    vat_parents = [
        {
            "account_name": "VAT Input",
            "parent_finder": lambda: find_tax_or_current_assets(company, "Asset")
        },
        {
            "account_name": "VAT Output", 
            "parent_finder": lambda: find_tax_or_current_liabilities(company, "Liability")
        },
        {
            "account_name": "Tax",
            "parent_finder": lambda: find_parent_account("Current Liabilities", company) or f"Liabilities - {company_abbr}"
        }
    ]
    
    # Check and create VAT parent accounts
    for vat_parent in vat_parents:
        account_name = vat_parent["account_name"]
        full_account_name = f"{account_name} - {company_abbr}"
        
        # Check if account exists (with or without company suffix)
        if not frappe.db.exists("Account", {"account_name": account_name, "company": company}):
            parent_account = vat_parent["parent_finder"]()
            
            if parent_account:
                try:
                    frappe.msgprint(f"Creating VAT parent account: {account_name}")
                    doc = frappe.new_doc("Account")
                    doc.account_name = account_name
                    doc.company = company
                    doc.parent_account = parent_account
                    doc.is_group = 1
                    doc.flags.ignore_permissions = True
                    doc.insert(ignore_if_duplicate=True)
                except Exception as e:
                    frappe.msgprint(f"Failed to create {account_name}: {str(e)}")
            else:
                frappe.msgprint(f"Could not determine parent account for {account_name}")

def check_base_chart_accounts(company):
    """Check if the base chart of accounts structure exists"""
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Check if base accounts exist
    base_accounts = ["Assets", "Liabilities", "Current Assets", "Current Liabilities"]
    missing_accounts = []
    
    for account in base_accounts:
        # Check with and without company suffix
        account_exists = frappe.db.exists("Account", {"account_name": account, "company": company})
        if not account_exists:
            missing_accounts.append(account)
    
    if missing_accounts:
        frappe.msgprint("The following base accounts are missing from your chart of accounts: " + 
                       ", ".join(missing_accounts) + 
                       ". Please ensure your chart of accounts is properly set up.")

def find_tax_or_current_assets(company, root_type):
    """Find Tax account under Current Assets, or Current Assets itself"""
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Try to find Tax account
    tax_account = frappe.db.exists("Account", {"account_name": "Tax", "company": company})
    if tax_account:
        return tax_account
    
    # Try to find Current Assets
    current_assets = frappe.db.exists("Account", {"account_name": "Current Assets", "company": company})
    if current_assets:
        return current_assets
    
    # Fall back to Assets root
    return f"Assets - {company_abbr}"

def find_tax_or_current_liabilities(company, root_type):
    """Find Tax account under Current Liabilities, or Current Liabilities itself"""
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # Try to find Tax account
    tax_account = frappe.db.exists("Account", {"account_name": "Tax", "company": company})
    if tax_account:
        return tax_account
    
    # Try to find Current Liabilities
    current_liabilities = frappe.db.exists("Account", {"account_name": "Current Liabilities", "company": company})
    if current_liabilities:
        return current_liabilities
    
    # Fall back to Liabilities root
    return f"Liabilities - {company_abbr}"

def find_parent_account(parent_name, company):
    """Find parent account with improved search for chart of accounts compatibility"""
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    
    # First check if the account exists with company suffix
    full_name = f"{parent_name} - {company_abbr}"
    if frappe.db.exists("Account", {"name": full_name, "company": company}):
        return full_name
    
    # Check if the account exists without company suffix
    # This is important when the chart of accounts has just been set up
    accounts = frappe.get_all(
        "Account", 
        filters={
            "account_name": parent_name,
            "company": company
        },
        fields=["name"]
    )
    if accounts:
        return accounts[0].name
    
    # Handle special cases for VAT accounts
    if parent_name == "VAT Input":
        # Try to find VAT Input under Tax, or directly under Current Assets
        tax_account = find_parent_account("Tax", company)
        if tax_account:
            # First try to see if "VAT Input" exists under Tax
            vat_accounts = frappe.get_all(
                "Account", 
                filters={
                    "account_name": "VAT Input",
                    "company": company,
                    "parent_account": tax_account
                },
                fields=["name"]
            )
            if vat_accounts:
                return vat_accounts[0].name
        
        # If not found under Tax, check directly under Current Assets
        current_assets = find_parent_account("Current Assets", company)
        if current_assets:
            return current_assets
        
    elif parent_name == "VAT Output" or parent_name == "Tax":
        # Similar logic for VAT Output or Tax
        # Try to find under Current Liabilities
        current_liabilities = find_parent_account("Current Liabilities", company)
        if current_liabilities:
            return current_liabilities
    
    # Fall back to root accounts
    root_type_map = {
        "VAT Input": "Asset",
        "VAT Output": "Liability",
        "Tax": "Liability",
        "Current Assets": "Asset",
        "Current Liabilities": "Liability"
    }
    
    if parent_name in root_type_map:
        root_type = root_type_map[parent_name]
        root_accounts = frappe.get_all(
            "Account", 
            filters={
                "company": company,
                "is_group": 1,
                "root_type": root_type,
                "parent_account": ["in", ["", None]]  # Top-level accounts
            },
            fields=["name"],
            order_by="name",
            limit=1
        )
        if root_accounts:
            return root_accounts[0].name
    
    # Last resort - try to find Assets or Liabilities root accounts
    root_name = None
    if parent_name in ["VAT Input", "Current Assets"]:
        root_name = f"Assets - {company_abbr}"
    elif parent_name in ["VAT Output", "Tax", "Current Liabilities"]:
        root_name = f"Liabilities - {company_abbr}"
    
    if root_name and frappe.db.exists("Account", {"name": root_name, "company": company}):
        return root_name
    
    # Absolutely last resort - any root account
    roots = frappe.get_all(
        "Account", 
        filters={
            "company": company,
            "is_group": 1,
            "parent_account": ["in", ["", None]]
        },
        fields=["name"],
        limit=1
    )
    if roots:
        return roots[0].name
    
    return None

def create_account(account_name, company, parent_account, is_group=0, account_type=None):
    """Create a new account"""
    # Extract account name without company suffix
    company_abbr = frappe.get_cached_value("Company", company, "abbr")
    account_name_without_abbr = account_name.replace(f" - {company_abbr}", "")
    
    doc = frappe.new_doc("Account")
    doc.account_name = account_name_without_abbr
    doc.company = company
    doc.parent_account = parent_account
    doc.is_group = is_group
    
    if account_type:
        doc.account_type = account_type
    
    doc.flags.ignore_permissions = True
    doc.insert(ignore_if_duplicate=True)
    
    return doc.name

def create_tax_template(template_data, company, doctype):
    """Create a tax template if it doesn't exist"""
    template = template_data.copy()
    template["company"] = company
    
    # Check if template already exists
    existing = frappe.db.exists(doctype, {"title": template["title"], "company": company})
    if existing:
        return
    
    # Create template
    doc = frappe.get_doc({
        "doctype": doctype,
        "title": template["title"],
        "company": company,
        "is_default": template.get("is_default", 0)
    })
    
    # Add taxes
    for tax in template["taxes"]:
        doc.append("taxes", {
            "charge_type": tax["charge_type"],
            "account_head": tax["account_head"],
            "description": tax["description"],
            "rate": tax["rate"],
            "add_deduct_tax": tax.get("add_deduct_tax", "Add")
        })
    
    # Insert with permissions ignored (for setup)
    doc.flags.ignore_permissions = True
    doc.insert()