import frappe
from frappe import _
import random
from frappe.utils import random_string

def create_sample_suppliers(company=None):
    """
    Create sample suppliers for testing all Cyprus VAT scenarios
    
    Args:
        company: Optional company to associate suppliers with
        
    Returns:
        Dict with information about created suppliers
    """
    # Validate company if provided
    if company and not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    # Make sure supplier groups exist
    ensure_supplier_groups_exist()
    
    # Define the sample suppliers to create
    sample_suppliers = [
        # Local suppliers (Cyprus VAT registered)
        {
            "supplier_name": "Cyprus Office Supplies Ltd",
            "supplier_group": "Commercial",
            "supplier_type": "Company",
            "country": "Cyprus",
            "tax_id": "CY10012345X",
            "description": "Local supplier for standard rate (19%) VAT"
        },
        {
            "supplier_name": "Cyprus Hotel Association",
            "supplier_group": "Services", 
            "supplier_type": "Company",
            "country": "Cyprus",
            "tax_id": "CY20023456Y",
            "description": "Local supplier for reduced rate (9%) VAT"
        },
        {
            "supplier_name": "Cyprus Books & Publishing",
            "supplier_group": "Raw Material",
            "supplier_type": "Company", 
            "country": "Cyprus",
            "tax_id": "CY30034567Z",
            "description": "Local supplier for super-reduced rate (5%) VAT"
        },
        {
            "supplier_name": "Cyprus Insurance Agency",
            "supplier_group": "Services",
            "supplier_type": "Company",
            "country": "Cyprus",
            "tax_id": "CY40045678A",
            "description": "Local supplier for exempt services"
        },
        
        # EU suppliers (for Intra-EU acquisition & B2B services)
        {
            "supplier_name": "German Electronics GmbH",
            "supplier_group": "Commercial",
            "supplier_type": "Company",
            "country": "Germany",
            "tax_id": "DE123456789",
            "description": "EU supplier for goods (intra-EU acquisition)"
        },
        {
            "supplier_name": "French IT Consulting SARL",
            "supplier_group": "Services",
            "supplier_type": "Company",
            "country": "France",
            "tax_id": "FR12345678901",
            "description": "EU supplier for services (reverse charge)"
        },
        {
            "supplier_name": "Italian Furniture Design SpA",
            "supplier_group": "Raw Material",
            "supplier_type": "Company",
            "country": "Italy",
            "tax_id": "IT12345678901",
            "description": "EU supplier for goods and installation (special case)"
        },
        
        # Non-EU suppliers (for imports)
        {
            "supplier_name": "UK Manufacturing Ltd",
            "supplier_group": "Commercial",
            "supplier_type": "Company",
            "country": "United Kingdom",
            "tax_id": "GB123456789",
            "description": "Non-EU supplier for import goods"
        },
        {
            "supplier_name": "US Software Inc",
            "supplier_group": "Services", 
            "supplier_type": "Company",
            "country": "United States",
            "description": "Non-EU supplier for digital services"
        },
        
        # Special cases
        {
            "supplier_name": "Global Dropshipping Services",
            "supplier_group": "Services",
            "supplier_type": "Company",
            "country": "Netherlands",
            "tax_id": "NL123456789B01",
            "description": "Triangulation case supplier"
        }
    ]
    
    # Create the suppliers
    suppliers_created = []
    
    for supplier_data in sample_suppliers:
        # Generate a unique name with suffix to avoid conflicts
        unique_suffix = random_string(5)
        supplier_data["supplier_name"] = f"{supplier_data['supplier_name']} - {unique_suffix}"
        
        # Check if supplier already exists
        existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_data["supplier_name"]})
        
        if existing:
            # Skip creation if exists (should not happen with random suffix)
            continue
        
        # Create new supplier
        supplier = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": supplier_data["supplier_name"],
            "supplier_group": supplier_data["supplier_group"],
            "supplier_type": supplier_data["supplier_type"],
            "country": supplier_data["country"],
            "tax_id": supplier_data.get("tax_id", ""),
            "supplier_details": supplier_data.get("description", "")
        })
        
        # Add company accounting details if company provided
        if company:
            default_payable_account = frappe.db.get_value("Company", company, "default_payable_account")
            if default_payable_account:
                supplier.append("accounts", {
                    "company": company,
                    "account": default_payable_account
                })
        
        supplier.insert()
        
        # Format for return info
        suppliers_created.append({
            "name": supplier.name,
            "supplier_name": supplier.supplier_name,
            "country": supplier.country,
            "tax_id": supplier.tax_id if supplier.tax_id else "N/A",
            "vat_scenario": supplier_data.get("description", "")
        })
    
    # Commit to save changes
    frappe.db.commit()
    
    # Return information about created suppliers
    return {
        "suppliers": suppliers_created,
        "count": len(suppliers_created),
        "message": _("Successfully created {0} sample suppliers").format(len(suppliers_created))
    }

@frappe.whitelist()
def delete_sample_suppliers(company=None):
    """
    Delete sample suppliers that were created for testing Cyprus VAT scenarios
    Uses the same list as create_sample_suppliers for consistency
    
    Args:
        company: Optional company (not used in this implementation)
        
    Returns:
        Dict with information about deleted suppliers
    """
    # Get base names from the same list used to create them
    base_supplier_names = [
        "Cyprus Office Supplies Ltd",
        "Cyprus Hotel Association",
        "Cyprus Books & Publishing",
        "Cyprus Insurance Agency",
        "German Electronics GmbH",
        "French IT Consulting SARL",
        "Italian Furniture Design SpA",
        "UK Manufacturing Ltd",
        "US Software Inc",
        "Global Dropshipping Services"
    ]
    
    # Track deletion results
    deletion_log = []
    errors = []
    
    # Find and delete suppliers that match the base names with any suffix
    for base_name in base_supplier_names:
        # Find all suppliers that start with this base name
        suppliers = frappe.get_all(
            "Supplier",
            filters={"supplier_name": ["like", f"{base_name} - %"]},
            fields=["name", "supplier_name", "country", "tax_id", "supplier_details"]
        )
        
        # Delete each matching supplier
        for supplier in suppliers:
            try:
                # Check for linked documents in a safer way
                has_links = False
                for doctype in ["Purchase Invoice", "Purchase Order", "Payment Entry"]:
                    if frappe.db.exists(doctype, {"supplier": supplier.name}):
                        has_links = True
                        errors.append({
                            "supplier": supplier.name,
                            "error": f"Cannot delete {supplier.supplier_name} as it has linked {doctype} documents"
                        })
                        break
                
                if has_links:
                    continue
                
                # Collect info before deletion
                deletion_log.append({
                    "name": supplier.name,
                    "supplier_name": supplier.supplier_name,
                    "country": supplier.country,
                    "tax_id": supplier.tax_id if supplier.tax_id else "N/A",
                    "description": supplier.supplier_details
                })
                
                # Delete the supplier
                frappe.delete_doc("Supplier", supplier.name)
                
            except Exception as e:
                errors.append({
                    "supplier": supplier.name,
                    "error": str(e)
                })
    
    # Commit changes
    frappe.db.commit()
    
    # Return results
    return {
        "deleted": deletion_log,
        "count": len(deletion_log),
        "errors": errors,
        "message": _("Successfully deleted {0} sample suppliers").format(len(deletion_log))
    }

def ensure_supplier_groups_exist():
    """Ensure that required supplier groups exist"""
    required_groups = ["Commercial", "Services", "Raw Material"]
    
    for group in required_groups:
        if not frappe.db.exists("Supplier Group", group):
            frappe.get_doc({
                "doctype": "Supplier Group",
                "supplier_group_name": group,
                "is_group": 0
            }).insert()