import frappe
from frappe import _

@frappe.whitelist()
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
    frappe.msgprint(_("Default accounts have been set for Cyprus company {0}.").format(company.name))

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