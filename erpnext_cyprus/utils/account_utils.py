import frappe
from frappe import _
from frappe.utils import cstr

def setup_cyprus_accounts(company):
    """
    Set up Cyprus-specific accounts in the chart of accounts
    """
    accounts_created = []
    
    # Define the Cyprus-specific accounts to be added
    cyprus_accounts = [
        # VAT-specific accounts under Duties and Taxes
        {
            "account_name": "VAT Cyprus Local (19%)",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "tax_rate": 19.0,
            "account_number": "2100",
        },
        {
            "account_name": "VAT Cyprus Reduced (9%)",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "tax_rate": 9.0,
            "account_number": "2110",
        },
        {
            "account_name": "VAT Cyprus Super Reduced (5%)",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "tax_rate": 5.0,
            "account_number": "2120",
        },
        {
            "account_name": "Intra-EU Acquisition VAT",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "account_number": "2200",
        },
        {
            "account_name": "Reverse Charge VAT B2B Services",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "account_number": "2300",
        },
        {
            "account_name": "Import VAT Non-EU",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "account_number": "2400",
        },
        {
            "account_name": "OSS VAT Digital Services",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "account_number": "2500",
        },
        
        # Income accounts by geography
        {
            "account_name": "Sales Cyprus",
            "parent_account": "Sales",
            "account_number": "4100",
        },
        {
            "account_name": "Sales EU B2B",
            "parent_account": "Sales",
            "account_number": "4200",
        },
        {
            "account_name": "Sales EU B2C",
            "parent_account": "Sales",
            "account_number": "4300",
        },
        {
            "account_name": "Sales Non-EU",
            "parent_account": "Sales",
            "account_number": "4400",
        },
        {
            "account_name": "Digital Services EU",
            "parent_account": "Service",
            "account_number": "4500",
        },
        {
            "account_name": "Services Cyprus",
            "parent_account": "Service",
            "account_number": "4600",
        },
        {
            "account_name": "Services EU B2B",
            "parent_account": "Service",
            "account_number": "4700",
        },
        {
            "account_name": "Services Non-EU",
            "parent_account": "Service",
            "account_number": "4800",
        }
    ]
    
    # First, ensure all parent accounts exist and are group accounts
    parent_accounts = set([account["parent_account"] for account in cyprus_accounts])
    for parent_name in parent_accounts:
        ensure_parent_account_is_group(parent_name, company)
    
    # Iterate through the accounts and create them if they don't exist
    for account_data in cyprus_accounts:
        account_name = account_data["account_name"]
        parent_account = account_data["parent_account"]
        
        # Check if account already exists by name or by function
        existing_account = find_existing_account(account_name, company)
        
        if existing_account:
            frappe.msgprint(_("Account {0} already exists. Skipping creation.").format(account_name))
            continue
            
        # Find the full parent account path
        parent = get_parent_account_path(parent_account, company)
        if not parent:
            frappe.msgprint(_("Parent account {0} not found. Skipping {1}").format(
                parent_account, account_name))
            continue
        
        # Create the account
        try:
            new_account = frappe.get_doc({
                "doctype": "Account",
                "account_name": account_name,
                "parent_account": parent,
                "company": company,
                "is_group": 0,
                "account_type": account_data.get("account_type", ""),
                "account_number": account_data.get("account_number", ""),
                "tax_rate": account_data.get("tax_rate", 0),
            })
            
            new_account.insert()
            accounts_created.append(account_name)
            frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error creating account {account_name}: {str(e)}", "Cyprus Chart of Accounts")
            frappe.msgprint(_("Error creating account {0}: {1}").format(account_name, str(e)))
            
    return accounts_created

def ensure_parent_account_is_group(parent_name, company):
    """
    Ensure the parent account exists and is set as a group account
    """
    parent_account = get_parent_account_path(parent_name, company)
    
    if parent_account:
        # Check if it's a group account
        is_group = frappe.db.get_value("Account", parent_account, "is_group")
        
        if not is_group:
            # Convert to group account
            frappe.db.set_value("Account", parent_account, "is_group", 1)
            frappe.msgprint(_("Converted {0} to a group account").format(parent_name))
            frappe.db.commit()
    else:
        frappe.msgprint(_("Parent account {0} not found in the chart of accounts").format(parent_name))

def find_existing_account(account_name, company):
    """
    Check if an account with the same name or similar function already exists
    """
    # Check by exact name
    existing = frappe.db.get_value("Account", 
        {"account_name": account_name, "company": company})
    
    if existing:
        return existing
        
    # Check by similar names (for broader matching)
    # For example, "VAT Cyprus Local" might exist as "Cyprus VAT" or "Local VAT (19%)"
    if "VAT" in account_name:
        similar_accounts = frappe.db.sql("""
            SELECT name FROM `tabAccount`
            WHERE account_name LIKE %s AND company = %s
        """, (f"%{account_name.split()[0]}%", company), as_dict=1)
        
        if similar_accounts and len(similar_accounts) > 0:
            return similar_accounts[0].name
            
    return None

def get_parent_account_path(parent_account, company):
    """
    Get the full account path for the parent account
    """
    # Try exact match first
    parent_data = frappe.db.get_value("Account", 
        {"account_name": parent_account, "company": company}, "name")
    
    if parent_data:
        return parent_data
        
    # If not found, try partial match
    accounts = frappe.db.sql("""
        SELECT name FROM `tabAccount`
        WHERE account_name LIKE %s AND company = %s
    """, (f"%{parent_account}%", company), as_dict=1)
    
    if accounts and len(accounts) > 0:
        return accounts[0].name
        
    return None