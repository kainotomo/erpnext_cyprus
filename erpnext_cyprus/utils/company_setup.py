import frappe
from frappe import _
from erpnext_cyprus.setup.company import setup_cyprus_company

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