import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_chart_of_accounts
from erpnext_cyprus.utils.tax_utils import (
    setup_purchase_tax_templates,
    setup_sales_tax_templates,
    setup_item_tax_templates,
    setup_tax_rules,
    setup_item_groups,
    setup_cyprus_territories
)

@frappe.whitelist()
def setup_cyprus_company(company):
    """
    Set up Cyprus-specific configuration for a company
    """
    frappe.msgprint(_("Starting Cyprus company setup for: {0}").format(company))
    
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    company_doc = frappe.get_doc("Company", company)
    if company_doc.country != "Cyprus":
        frappe.throw(_("This function is only available for Cyprus-based companies"))
    
    results = {
        "message": _("Cyprus company setup completed"),
        "accounts_added": [],
        "item_groups_added": [],
        "purchase_templates_added": [],
        "sales_templates_added": [],
        "item_tax_templates_added": [],
        "tax_rules_added": [],
        "territories_added": []
    }
    
    # Step 1: Setup chart of accounts
    frappe.msgprint(_("Step 1: Setting up chart of accounts"))
    accounts_created = setup_chart_of_accounts(company)
    results["accounts_added"] = accounts_created
    frappe.msgprint(_("Chart of accounts setup completed. Created: {0}").format(
        ", ".join(accounts_created) if accounts_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 1.5: Setup territories (between steps 1 and 2)
    frappe.msgprint(_("Setting up territories"))
    territories_created = setup_cyprus_territories()
    results["territories_added"] = territories_created
    frappe.msgprint(_("Territories setup completed. Created: {0}").format(
        ", ".join(territories_created) if territories_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 2: Setup required item groups
    frappe.msgprint(_("Step 2: Setting up required item groups"))
    item_groups_created = setup_item_groups()  # Corrected
    results["item_groups_added"] = item_groups_created
    frappe.msgprint(_("Item groups setup completed. Created: {0}").format(
        ", ".join(item_groups_created) if item_groups_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 3: Setup purchase tax templates
    frappe.msgprint(_("Step 3: Setting up purchase tax templates"))
    purchase_templates_created = setup_purchase_tax_templates(company)  # Corrected
    results["purchase_templates_added"] = purchase_templates_created
    frappe.msgprint(_("Purchase tax templates setup completed. Created: {0}").format(
        ", ".join(purchase_templates_created) if purchase_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 4: Setup sales tax templates
    frappe.msgprint(_("Step 4: Setting up sales tax templates"))
    sales_templates_created = setup_sales_tax_templates(company)  # Corrected
    results["sales_templates_added"] = sales_templates_created
    frappe.msgprint(_("Sales tax templates setup completed. Created: {0}").format(
        ", ".join(sales_templates_created) if sales_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 5: Setup item tax templates
    frappe.msgprint(_("Step 5: Setting up item tax templates"))
    item_templates_created = setup_item_tax_templates(company)  # Corrected
    results["item_tax_templates_added"] = item_templates_created
    frappe.msgprint(_("Item tax templates setup completed. Created: {0}").format(
        ", ".join(item_templates_created) if item_templates_created else "None"))
    
    # Commit changes before proceeding
    frappe.db.commit()
    
    # Step 6: Setup tax rules
    frappe.msgprint(_("Step 6: Setting up tax rules"))
    tax_rules_created = setup_tax_rules(company)  # Corrected
    results["tax_rules_added"] = tax_rules_created
    frappe.msgprint(_("Tax rules setup completed. Created: {0}").format(
        ", ".join(tax_rules_created) if tax_rules_created else "None"))
    
    return results
