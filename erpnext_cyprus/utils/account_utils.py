import frappe
from frappe import _
from frappe.utils import cstr

def setup_cyprus_accounts(company):
    """
    Set up Cyprus-specific accounts in the chart of accounts
    """
    accounts_created = []
    
    # First, check if company uses account numbers and determine the pattern
    account_number_info = get_account_number_info(company)
    
    # Get existing account numbers to avoid conflicts
    existing_account_numbers = get_existing_account_numbers(company)
    
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
    
    cyprus_salary_accounts = [
        # Employer contributions
        {
            "account_name": "Employer Social Insurance",
            "parent_account": "Indirect Expenses",
            "account_number": "6100"
        },
        {
            "account_name": "Employer GESY Contributions",
            "parent_account": "Indirect Expenses",
            "account_number": "6110"
        },
        {
            "account_name": "Redundancy Fund",
            "parent_account": "Indirect Expenses",
            "account_number": "6120"
        },
        {
            "account_name": "Industrial Training Fund",
            "parent_account": "Indirect Expenses",
            "account_number": "6130"
        },
        {
            "account_name": "Social Cohesion Fund",
            "parent_account": "Indirect Expenses",
            "account_number": "6140"
        },
        
        # Employee withholdings (liabilities)
        {
            "account_name": "Employee Income Tax Payable",
            "parent_account": "Duties and Taxes",
            "account_type": "Tax",
            "account_number": "2600"
        },
        {
            "account_name": "Employee Social Insurance Payable",
            "parent_account": "Duties and Taxes",
            "account_number": "2610"
        },
        {
            "account_name": "Employee GESY Payable",
            "parent_account": "Duties and Taxes",
            "account_number": "2620"
        },
        
        # Salary types
        {
            "account_name": "Basic Salaries",
            "parent_account": "Salary",
            "account_number": "6000"
        },
        {
            "account_name": "13th Month Salary",
            "parent_account": "Salary",
            "account_number": "6010"
        },
        {
            "account_name": "Bonus Payments",
            "parent_account": "Salary",
            "account_number": "6020"
        },
        {
            "account_name": "Director Remuneration",
            "parent_account": "Salary",
            "account_number": "6030"
        }
    ]
    
    # Combine all accounts
    all_accounts = cyprus_accounts + cyprus_salary_accounts
    
    # Adjust account numbers based on existing pattern or remove if not used
    if not account_number_info["uses_account_numbers"]:
        # If company doesn't use account numbers, remove them
        for account in all_accounts:
            if "account_number" in account:
                del account["account_number"]
        frappe.msgprint(_("Account numbers removed as the company does not use them"))
    else:
        # If company uses account numbers, adjust to follow the pattern and resolve conflicts
        adjust_account_numbers(all_accounts, account_number_info, existing_account_numbers)
    
    # First, ensure all parent accounts exist and are group accounts
    parent_accounts = set([account["parent_account"] for account in all_accounts])
    for parent_name in parent_accounts:
        ensure_parent_account_is_group(parent_name, company)
    
    # Iterate through the accounts and create them if they don't exist
    for account_data in all_accounts:
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

def get_account_number_info(company):
    """
    Check if the company uses account numbers and identify the pattern
    """
    # Get a sample of accounts to check
    accounts = frappe.get_all(
        "Account",
        filters={"company": company},
        fields=["name", "account_number", "account_name", "parent_account", "root_type"],
        limit=50
    )
    
    # Initialize result
    result = {
        "uses_account_numbers": False,
        "digit_count": 0,
        "root_type_patterns": {},
        "parent_patterns": {}
    }
    
    # Check if account numbers are used
    accounts_with_numbers = [a for a in accounts if a.account_number]
    if not accounts_with_numbers:
        return result
    
    # Company uses account numbers
    result["uses_account_numbers"] = True
    
    # Analyze pattern
    digit_counts = {}
    for acc in accounts_with_numbers:
        digits = len(acc.account_number)
        digit_counts[digits] = digit_counts.get(digits, 0) + 1
        
        # Track patterns by root type
        if acc.root_type:
            if acc.root_type not in result["root_type_patterns"]:
                result["root_type_patterns"][acc.root_type] = []
            result["root_type_patterns"][acc.root_type].append(acc.account_number)
        
        # Track patterns by parent account
        if acc.parent_account:
            parent_key = acc.parent_account.split(" - ")[0]  # Remove company suffix
            if parent_key not in result["parent_patterns"]:
                result["parent_patterns"][parent_key] = []
            result["parent_patterns"][parent_key].append(acc.account_number)
    
    # Determine most common digit count
    if digit_counts:
        result["digit_count"] = max(digit_counts, key=digit_counts.get)
    
    return result

def get_existing_account_numbers(company):
    """
    Get all existing account numbers to avoid conflicts
    """
    accounts = frappe.get_all(
        "Account",
        filters={"company": company},
        fields=["name", "account_number", "account_name"],
    )
    
    account_numbers = {}
    for acc in accounts:
        if acc.account_number:
            account_numbers[acc.account_number] = acc.account_name
    
    return account_numbers

def adjust_account_numbers(accounts, account_number_info, existing_account_numbers):
    """
    Adjust account numbers to match the company's pattern and resolve conflicts
    """
    digit_count = account_number_info["digit_count"]
    
    if digit_count == 0:
        return
    
    for account in accounts:
        if "account_number" in account:
            # Pad with zeros if needed
            original_number = account["account_number"]
            account["account_number"] = original_number.zfill(digit_count)
            
            # Check for conflicts with existing account numbers
            if account["account_number"] in existing_account_numbers:
                # Generate an alternative account number
                alternative_number = find_alternative_account_number(
                    account["account_number"],
                    existing_account_numbers,
                    digit_count
                )
                
                frappe.msgprint(_(
                    "Account number {0} already used by '{1}'. Using alternative: {2} for '{3}'"
                ).format(
                    account["account_number"],
                    existing_account_numbers[account["account_number"]],
                    alternative_number,
                    account["account_name"]
                ))
                
                account["account_number"] = alternative_number
                
            # Add to existing numbers to prevent conflicts between new accounts
            existing_account_numbers[account["account_number"]] = account["account_name"]
            
            # Check for parent account patterns - only if we didn't need to generate an alternative
            if account["account_number"].startswith(original_number):  # No conflict occurred
                parent = account["parent_account"]
                parent_patterns = account_number_info["parent_patterns"].get(parent, [])
                
                if parent_patterns:
                    # Try to follow the pattern of siblings
                    first_digits = None
                    
                    # Look for a pattern in first digits of siblings
                    for pattern in parent_patterns:
                        if len(pattern) >= 2:
                            if first_digits is None:
                                first_digits = pattern[:2]
                            elif first_digits != pattern[:2]:
                                first_digits = None
                                break
                    
                    # If consistent pattern found, apply it
                    if first_digits and len(account["account_number"]) >= 2:
                        account["account_number"] = first_digits + account["account_number"][2:]

def find_alternative_account_number(original_number, existing_numbers, digit_count):
    """
    Generate an alternative account number to resolve conflicts
    """
    for i in range(1, 1000):
        alternative_number = str(int(original_number) + i).zfill(digit_count)
        if alternative_number not in existing_numbers:
            return alternative_number
    
    frappe.throw(_("Unable to generate a unique account number for {0}").format(original_number))