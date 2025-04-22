import frappe
from frappe import _
from frappe.utils import cstr
from erpnext_cyprus.utils.account_utils import setup_cyprus_accounts
from erpnext_cyprus.utils.tax_utils import (
    setup_purchase_tax_templates,
    setup_sales_tax_templates,
    setup_item_tax_templates,
    setup_tax_rules,
    setup_item_groups
)
from erpnext_cyprus.utils.create_sample_data import (
    create_sample_suppliers,
    delete_sample_suppliers,
    create_sample_customers,
    delete_sample_customers,
    create_sample_items,
    delete_sample_items,
    create_sample_purchase_invoices,
    delete_sample_purchase_invoices,
    create_sample_sales_invoices,
    delete_sample_sales_invoices
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
        "tax_rules_added": []
    }
    
    # Step 1: Setup chart of accounts
    frappe.msgprint(_("Step 1: Setting up chart of accounts"))
    accounts_created = setup_cyprus_accounts(company)
    results["accounts_added"] = accounts_created
    frappe.msgprint(_("Chart of accounts setup completed. Created: {0}").format(
        ", ".join(accounts_created) if accounts_created else "None"))
    
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

@frappe.whitelist()
def create_sample_data(company=None):
    """
    Create complete sample data for testing Cyprus VAT scenarios
    including suppliers, customers, items and invoices
    
    Args:
        company: Company to associate with sample data (required for invoices)
        
    Returns:
        Dict with results of sample data creation
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    if not company:
        frappe.throw(_("Company is required to create complete sample data"))
        
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    results = {
        "message": _("Sample data creation completed"),
    }
    
    # Step 1: Create sample suppliers
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Creating suppliers..."),
        percent=20,
        doctype=None,
        docname=None
    )
    
    supplier_results = create_sample_suppliers(company)
    results["suppliers"] = supplier_results["suppliers"]
    results["suppliers_count"] = supplier_results["count"]
    
    # Step 2: Create sample customers
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Creating customers..."),
        percent=40,
        doctype=None,
        docname=None
    )
    
    customer_results = create_sample_customers(company)
    results["customers"] = customer_results["customers"]
    results["customers_count"] = customer_results["count"]
    
    # Step 3: Create sample items
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Creating items..."),
        percent=60,
        doctype=None,
        docname=None
    )
    
    item_results = create_sample_items(company)
    results["items"] = item_results["items"]
    results["items_count"] = item_results["count"]
    
    # Step 4: Create purchase invoices
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Creating purchase invoices..."),
        percent=80,
        doctype=None,
        docname=None
    )
    
    pi_results = create_sample_purchase_invoices(company)
    results["purchase_invoices"] = pi_results["invoices"]
    results["purchase_count"] = pi_results["count"]
    
    # Step 5: Create sales invoices
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Creating sales invoices..."),
        percent=90,
        doctype=None,
        docname=None
    )
    
    si_results = create_sample_sales_invoices(company)
    results["sales_invoices"] = si_results["invoices"]
    results["sales_count"] = si_results["count"]
    
    frappe.publish_progress(
        title=_("Creating Sample Data"),
        description=_("Completed"),
        percent=100,
        doctype=None,
        docname=None
    )
    
    return results

@frappe.whitelist()
def delete_sample_data(company=None):
    """
    Delete all sample data created for testing Cyprus VAT scenarios
    including invoices, items, customers and suppliers
    
    Args:
        company: Optional company filter (used only for certain data types)
        
    Returns:
        Dict with results of sample data deletion
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    results = {
        "message": _("Sample data deletion completed"),
    }
    
    # Step 1: Delete sales invoices
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Deleting sales invoices..."),
        percent=20,
        doctype=None,
        docname=None
    )
    
    si_results = delete_sample_sales_invoices()
    results["sales_deleted"] = si_results["count"]
    results["sales_errors"] = si_results["errors"]
    
    # Step 2: Delete purchase invoices
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Deleting purchase invoices..."),
        percent=40,
        doctype=None,
        docname=None
    )
    
    pi_results = delete_sample_purchase_invoices()
    results["purchase_deleted"] = pi_results["count"]
    results["purchase_errors"] = pi_results["errors"]
    
    # Step 3: Delete sample items
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Deleting items..."),
        percent=60,
        doctype=None,
        docname=None
    )
    
    item_results = delete_sample_items()
    results["items_deleted"] = item_results["count"]
    results["items_errors"] = item_results["errors"]
    
    # Step 4: Delete sample customers
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Deleting customers..."),
        percent=80,
        doctype=None,
        docname=None
    )
    
    customer_results = delete_sample_customers(company)
    results["customers_deleted"] = customer_results["count"]
    results["customers_errors"] = customer_results["errors"]
    
    # Step 5: Delete sample suppliers
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Deleting suppliers..."),
        percent=90,
        doctype=None,
        docname=None
    )
    
    supplier_results = delete_sample_suppliers(company)
    results["suppliers_deleted"] = supplier_results["count"]
    results["suppliers_errors"] = supplier_results["errors"]
    
    frappe.publish_progress(
        title=_("Deleting Sample Data"),
        description=_("Completed"),
        percent=100,
        doctype=None,
        docname=None
    )
    
    return results

@frappe.whitelist()
def create_sample_invoices(company=None):
    """
    Create sample sales and purchase invoices for testing Cyprus VAT scenarios
    
    Args:
        company: Company to create invoices for (required)
        
    Returns:
        Dict with results of invoice creation
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    if not company:
        frappe.throw(_("Company is required to create sample invoices"))
        
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    results = {
        "message": _("Sample invoice creation completed"),
    }
    
    # Create purchase invoices
    pi_results = create_sample_purchase_invoices(company)
    results["purchase_invoices"] = pi_results["invoices"]
    results["purchase_count"] = pi_results["count"]
    
    # Create sales invoices
    si_results = create_sample_sales_invoices(company)
    results["sales_invoices"] = si_results["invoices"]
    results["sales_count"] = si_results["count"]
    
    return results

@frappe.whitelist()
def delete_sample_invoices():
    """
    Delete sample sales and purchase invoices created for testing Cyprus VAT scenarios
    
    Returns:
        Dict with results of invoice deletion
    """
    if not frappe.has_permission("Company", "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    
    results = {
        "message": _("Sample invoice deletion completed"),
    }
    
    # Delete purchase invoices
    pi_results = delete_sample_purchase_invoices()
    results["purchase_deleted"] = pi_results["count"]
    results["purchase_errors"] = pi_results["errors"]
    
    # Delete sales invoices
    si_results = delete_sample_sales_invoices()
    results["sales_deleted"] = si_results["count"]
    results["sales_errors"] = si_results["errors"]
    
    return results
