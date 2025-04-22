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
        
        # Create address for supplier with required fields
        address = frappe.get_doc({
            "doctype": "Address",
            "address_title": supplier_data["supplier_name"],
            "address_type": "Billing",
            "address_line1": f"Business Address, {supplier_data['country']}",  # Added required field
            "city": get_default_city_for_country(supplier_data['country']),     # Added required field
            "country": supplier_data["country"],
            "is_primary_address": 1,
            "is_shipping_address": 1
        })
        
        # Link address to supplier
        address.append("links", {
            "link_doctype": "Supplier",
            "link_name": supplier.name
        })
        address.insert()
        
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

@frappe.whitelist()
def create_sample_customers(company=None):
    """
    Create sample customers for testing Cyprus VAT scenarios
    
    Args:
        company: Optional company to associate customers with
        
    Returns:
        Dict with information about created customers
    """
    # Validate company if provided
    if company and not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    # Make sure customer groups exist
    ensure_customer_groups_exist()
    
    # Define the sample customers to create
    sample_customers = [
        # Local customers (Cyprus)
        {
            "customer_name": "Cyprus Retail Consumer",
            "customer_group": "Individual",
            "customer_type": "Individual",
            "country": "Cyprus",
            "tax_id": "",
            "description": "Local consumer for standard domestic sales"
        },
        {
            "customer_name": "Cyprus Business Ltd",
            "customer_group": "Commercial",
            "customer_type": "Company",
            "country": "Cyprus",
            "tax_id": "CY10012345X",
            "description": "Local business with VAT registration"
        },
        
        # EU customers - B2B with VAT numbers
        {
            "customer_name": "German Corporation GmbH",
            "customer_group": "Commercial",
            "customer_type": "Company",
            "country": "Germany",
            "tax_id": "DE123456789",
            "description": "EU B2B customer with valid VAT (reverse charge)"
        },
        {
            "customer_name": "French Enterprise SARL",
            "customer_group": "Commercial", 
            "customer_type": "Company",
            "country": "France",
            "tax_id": "FR12345678901",
            "description": "EU B2B customer with valid VAT (reverse charge)"
        },
        
        # EU customers - B2C without VAT numbers
        {
            "customer_name": "Maria Schmidt",
            "customer_group": "Individual",
            "customer_type": "Individual",
            "country": "Germany",
            "tax_id": "",
            "description": "EU individual consumer (B2C) - subject to OSS for digital services"
        },
        {
            "customer_name": "Pierre Dubois",
            "customer_group": "Individual",
            "customer_type": "Individual",
            "country": "France",
            "tax_id": "",
            "description": "EU individual consumer (B2C) - subject to OSS for digital services"
        },
        
        # EU Distance Selling customer
        {
            "customer_name": "Italian Small Business",
            "customer_group": "Individual",  # Treated as B2C until VAT threshold
            "customer_type": "Company",
            "country": "Italy",
            "tax_id": "",  # No VAT number
            "description": "EU business without VAT registration (distance selling rules)"
        },
        
        # Non-EU customers
        {
            "customer_name": "UK Trading Ltd",
            "customer_group": "Commercial",
            "customer_type": "Company",
            "country": "United Kingdom",
            "tax_id": "GB123456789",
            "description": "Non-EU business customer (export)"
        },
        {
            "customer_name": "US Corporation Inc",
            "customer_group": "Commercial", 
            "customer_type": "Company",
            "country": "United States",
            "tax_id": "",
            "description": "Non-EU business customer (export)"
        },
        {
            "customer_name": "John Smith",
            "customer_group": "Individual",
            "customer_type": "Individual",
            "country": "United States",
            "tax_id": "",
            "description": "Non-EU individual customer (export)"
        }
    ]
    
    # Create the customers
    customers_created = []
    
    for customer_data in sample_customers:
        # Generate a unique name with suffix to avoid conflicts
        unique_suffix = random_string(5)
        customer_data["customer_name"] = f"{customer_data['customer_name']} - {unique_suffix}"
        
        # Check if customer already exists
        existing = frappe.db.get_value("Customer", {"customer_name": customer_data["customer_name"]})
        
        if existing:
            # Skip creation if exists (should not happen with random suffix)
            continue
        
        # Create new customer
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_data["customer_name"],
            "customer_group": customer_data["customer_group"],
            "customer_type": customer_data["customer_type"],
            "territory": "All Territories",
            "customer_details": customer_data.get("description", "")
        })
        
        # Add VAT if provided
        if customer_data.get("tax_id"):
            customer.tax_id = customer_data["tax_id"]
        
        # Add company accounting details if company provided
        if company:
            default_receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")
            if default_receivable_account:
                customer.append("accounts", {
                    "company": company,
                    "account": default_receivable_account
                })
        
        # Insert customer
        customer.insert()
        
        # Create address with required fields
        address = frappe.get_doc({
            "doctype": "Address",
            "address_title": customer_data["customer_name"],
            "address_type": "Billing",
            "address_line1": f"Street Address, {customer_data['country']}", # Added required field
            "city": get_default_city_for_country(customer_data['country']), # Added required field
            "country": customer_data["country"],
            "is_primary_address": 1,
            "is_shipping_address": 1
        })
        
        # Link address to customer
        address.append("links", {
            "link_doctype": "Customer",
            "link_name": customer.name
        })
        address.insert()
        
        # Format for return info
        customers_created.append({
            "name": customer.name,
            "customer_name": customer.customer_name,
            "country": customer_data["country"],
            "customer_group": customer.customer_group,
            "tax_id": customer.tax_id if customer.tax_id else "N/A",
            "vat_scenario": customer_data.get("description", "")
        })
    
    # Commit to save changes
    frappe.db.commit()
    
    # Return information about created customers
    return {
        "customers": customers_created,
        "count": len(customers_created),
        "message": _("Successfully created {0} sample customers").format(len(customers_created))
    }

@frappe.whitelist()
def delete_sample_customers(company=None):
    """
    Delete sample customers that were created for testing Cyprus VAT scenarios
    Uses the same list as create_sample_customers for consistency
    
    Args:
        company: Optional company (not used in this implementation)
        
    Returns:
        Dict with information about deleted customers
    """
    # Get base names from the same list used to create them
    base_customer_names = [
        "Cyprus Retail Consumer",
        "Cyprus Business Ltd",
        "German Corporation GmbH",
        "French Enterprise SARL",
        "Maria Schmidt",
        "Pierre Dubois",
        "Italian Small Business",
        "UK Trading Ltd",
        "US Corporation Inc",
        "John Smith"
    ]
    
    # Track deletion results
    deletion_log = []
    errors = []
    
    # Find and delete customers that match the base names with any suffix
    for base_name in base_customer_names:
        # Find all customers that start with this base name
        customers = frappe.get_all(
            "Customer",
            filters={"customer_name": ["like", f"{base_name} - %"]},
            fields=["name", "customer_name", "customer_group", "tax_id", "customer_details"]
        )
        
        # Delete each matching customer
        for customer in customers:
            try:
                # Check for linked documents
                has_links = False
                for doctype in ["Sales Invoice", "Sales Order", "Payment Entry", "Delivery Note"]:
                    if frappe.db.exists(doctype, {"customer": customer.name}):
                        has_links = True
                        errors.append({
                            "customer": customer.name,
                            "error": f"Cannot delete {customer.customer_name} as it has linked {doctype} documents"
                        })
                        break
                
                if has_links:
                    continue
                
                # Find and delete linked addresses
                addresses = frappe.get_all(
                    "Dynamic Link",
                    filters={"link_doctype": "Customer", "link_name": customer.name},
                    fields=["parent"]
                )
                
                for addr in addresses:
                    try:
                        frappe.delete_doc("Address", addr.parent)
                    except Exception as e:
                        errors.append({
                            "customer": customer.name,
                            "error": f"Error deleting address {addr.parent}: {str(e)}"
                        })
                
                # Collect info before deletion
                deletion_log.append({
                    "name": customer.name,
                    "customer_name": customer.customer_name,
                    "customer_group": customer.customer_group,
                    "tax_id": customer.tax_id if customer.tax_id else "N/A",
                    "description": customer.customer_details
                })
                
                # Delete the customer
                frappe.delete_doc("Customer", customer.name)
                
            except Exception as e:
                errors.append({
                    "customer": customer.name,
                    "error": str(e)
                })
    
    # Commit changes
    frappe.db.commit()
    
    # Return results
    return {
        "deleted": deletion_log,
        "count": len(deletion_log),
        "errors": errors,
        "message": _("Successfully deleted {0} sample customers").format(len(deletion_log))
    }

def ensure_customer_groups_exist():
    """Ensure that required customer groups exist"""
    required_groups = ["Individual", "Commercial"]
    
    for group in required_groups:
        if not frappe.db.exists("Customer Group", group):
            frappe.get_doc({
                "doctype": "Customer Group",
                "customer_group_name": group,
                "is_group": 0
            }).insert()

# Helper function to provide appropriate city names for different countries
def get_default_city_for_country(country):
    """Return a typical city name for the given country"""
    city_map = {
        "Cyprus": "Nicosia",
        "Germany": "Berlin",
        "France": "Paris",
        "Italy": "Rome",
        "United Kingdom": "London",
        "United States": "New York",
        "Netherlands": "Amsterdam",
        "Spain": "Madrid",
        "Greece": "Athens",
        "Belgium": "Brussels"
    }
    
    return city_map.get(country, "Main City")  # Default to "Main City" if country not in map

@frappe.whitelist()
def create_sample_items(company=None):
    """
    Create sample items for testing Cyprus VAT scenarios
    
    Args:
        company: Optional company to associate items with (for item defaults)
        
    Returns:
        Dict with information about created items
    """
    # Validate company if provided
    if company and not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist").format(company))
    
    # Define the sample items to create
    sample_items = [
        # Standard rate (19%) items
        {
            "item_name": "Office Desk",
            "item_group": "Products",
            "item_code": "CY-STD-DESK",
            "description": "Office desk with standard 19% VAT rate",
            "is_stock_item": 1,
            "standard_rate": 350.00,
            "vat_rate": 19,
            "stock_uom": "Nos"
        },
        {
            "item_name": "Laptop Computer",
            "item_group": "Products",
            "item_code": "CY-STD-LAPTOP",
            "description": "Business laptop with standard 19% VAT rate",
            "is_stock_item": 1,
            "standard_rate": 850.00,
            "vat_rate": 19,
            "stock_uom": "Nos"
        },
        {
            "item_name": "IT Support Services",
            "item_group": "Services",
            "item_code": "CY-STD-ITSUPPORT",
            "description": "Technical IT support with standard 19% VAT rate",
            "is_stock_item": 0,
            "standard_rate": 80.00,
            "vat_rate": 19,
            "stock_uom": "Hour"
        },
        
        # Reduced rate (9%) items
        {
            "item_name": "Hotel Accommodation",
            "item_group": "Services",
            "item_code": "CY-RED-HOTEL",
            "description": "Hotel accommodation with reduced 9% VAT rate",
            "is_stock_item": 0,
            "standard_rate": 120.00,
            "vat_rate": 9,
            "stock_uom": "Day"
        },
        {
            "item_name": "Restaurant Meal",
            "item_group": "Products",
            "item_code": "CY-RED-MEAL",
            "description": "Restaurant meal with reduced 9% VAT rate",
            "is_stock_item": 1,
            "standard_rate": 25.00,
            "vat_rate": 9,
            "stock_uom": "Nos"
        },
        
        # Super-reduced rate (5%) items
        {
            "item_name": "Educational Book",
            "item_group": "Products",
            "item_code": "CY-SRED-BOOK",
            "description": "Educational book with super-reduced 5% VAT rate",
            "is_stock_item": 1,
            "standard_rate": 35.00,
            "vat_rate": 5,
            "stock_uom": "Nos"
        },
        {
            "item_name": "Pharmaceutical Product",
            "item_group": "Products",
            "item_code": "CY-SRED-PHARMA",
            "description": "Pharmaceutical product with super-reduced 5% VAT rate",
            "is_stock_item": 1,
            "standard_rate": 18.50,
            "vat_rate": 5,
            "stock_uom": "Nos"
        },
        
        # Zero-rated items
        {
            "item_name": "Export Goods",
            "item_group": "Products",
            "item_code": "CY-ZERO-EXPORT",
            "description": "Goods for export with zero VAT rate",
            "is_stock_item": 1,
            "standard_rate": 200.00,
            "vat_rate": 0,
            "stock_uom": "Nos"
        },
        
        # Exempt items
        {
            "item_name": "Insurance Service",
            "item_group": "Services",
            "item_code": "CY-EXEMPT-INS",
            "description": "Insurance service exempt from VAT",
            "is_stock_item": 0,
            "standard_rate": 150.00,
            "vat_rate": 0,
            "is_exempt": 1,
            "stock_uom": "Nos"
        },
        {
            "item_name": "Medical Service",
            "item_group": "Services",
            "item_code": "CY-EXEMPT-MED",
            "description": "Medical service exempt from VAT",
            "is_stock_item": 0,
            "standard_rate": 80.00,
            "vat_rate": 0,
            "is_exempt": 1,
            "stock_uom": "Hour"
        },
        
        # Digital services (for OSS testing)
        {
            "item_name": "Digital Subscription",
            "item_group": "Services",
            "item_code": "CY-DIG-SUB",
            "description": "Digital subscription service for OSS VAT testing",
            "is_stock_item": 0,
            "standard_rate": 9.99,
            "vat_rate": 19,  # Default Cyprus rate, but will be taxed at destination rate
            "is_digital": 1,
            "stock_uom": "Nos"
        },
        
        # Items for triangular transactions
        {
            "item_name": "Triangulation Goods",
            "item_group": "Products",
            "item_code": "CY-TRI-GOODS",
            "description": "Goods for testing triangulation scenarios",
            "is_stock_item": 1,
            "standard_rate": 450.00,
            "vat_rate": 0,  # Zero-rated for triangulation
            "stock_uom": "Nos"
        }
    ]
    
    # Create the items
    items_created = []
    
    # Ensure required item groups exist
    ensure_item_groups_exist()
    
    for item_data in sample_items:
        # Check if item already exists by item code
        existing = frappe.db.exists("Item", item_data["item_code"])
        
        if existing:
            # Update existing item instead of creating new
            item = frappe.get_doc("Item", existing)
            item.item_name = item_data["item_name"]
            item.description = item_data["description"]
            item.item_group = item_data["item_group"]
            item.is_stock_item = item_data["is_stock_item"]
            item.standard_rate = item_data["standard_rate"]
            item.save()
        else:
            # Create new item
            item = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_data["item_code"],
                "item_name": item_data["item_name"],
                "description": item_data["description"],
                "item_group": item_data["item_group"],
                "is_stock_item": item_data["is_stock_item"],
                "stock_uom": item_data["stock_uom"],
                "standard_rate": item_data["standard_rate"]
            })
            
            # Add VAT/tax classification in item flags or custom fields
            if item_data.get("is_exempt"):
                item.is_exempted = 1
            
            if item_data.get("is_digital"):
                # Flag for digital services if your system supports it
                # This might be a custom field in your implementation
                # item.digital_service = 1
                pass
                
            # If company is provided, add item defaults
            if company:
                item.append("item_defaults", {
                    "company": company,
                    "default_warehouse": frappe.db.get_value("Warehouse", {"company": company, "is_group": 0}, "name"),
                    "default_price_list": frappe.db.get_value("Price List", {"selling": 1}, "name")
                })
            
            item.insert()
            
            # Create and link item tax template based on VAT rate
            link_item_tax_template(item, company, item_data["vat_rate"], item_data.get("is_exempt"))
        
        # Add to created items list
        items_created.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "item_group": item.item_group,
            "vat_rate": item_data["vat_rate"],
            "exempt": item_data.get("is_exempt", 0),
            "digital": item_data.get("is_digital", 0)
        })
    
    # Commit to save changes
    frappe.db.commit()
    
    # Return information about created items
    return {
        "items": items_created,
        "count": len(items_created),
        "message": _("Successfully created/updated {0} sample items").format(len(items_created))
    }

@frappe.whitelist()
def delete_sample_items():
    """
    Delete sample items that were created for testing Cyprus VAT scenarios
    
    Returns:
        Dict with information about deleted items
    """
    # Get item codes from the list we created
    item_codes = [
        "CY-STD-DESK", "CY-STD-LAPTOP", "CY-STD-ITSUPPORT", 
        "CY-RED-HOTEL", "CY-RED-MEAL",
        "CY-SRED-BOOK", "CY-SRED-PHARMA", 
        "CY-ZERO-EXPORT", 
        "CY-EXEMPT-INS", "CY-EXEMPT-MED", 
        "CY-DIG-SUB", 
        "CY-TRI-GOODS"
    ]
    
    # Track deletion results
    deletion_log = []
    errors = []
    
    # Try to delete each item
    for item_code in item_codes:
        if frappe.db.exists("Item", item_code):
            try:
                # Check for linked documents
                has_links = False
                for doctype in ["Sales Invoice Item", "Purchase Invoice Item", "Sales Order Item"]:
                    links = frappe.db.get_all(doctype, filters={"item_code": item_code}, limit=1)
                    if links:
                        has_links = True
                        errors.append({
                            "item_code": item_code,
                            "error": f"Cannot delete {item_code} as it has linked {doctype} entries"
                        })
                        break
                
                if has_links:
                    continue
                
                # Get item details before deletion
                item = frappe.get_doc("Item", item_code)
                
                # Delete the item
                frappe.delete_doc("Item", item_code)
                
                # Record the deletion
                deletion_log.append({
                    "item_code": item_code,
                    "item_name": item.item_name,
                    "item_group": item.item_group
                })
                
            except Exception as e:
                errors.append({
                    "item_code": item_code,
                    "error": str(e)
                })
    
    # Commit changes
    frappe.db.commit()
    
    # Return results
    return {
        "deleted": deletion_log,
        "count": len(deletion_log),
        "errors": errors,
        "message": _("Successfully deleted {0} sample items").format(len(deletion_log))
    }

def ensure_item_groups_exist():
    """Ensure that required item groups exist"""
    required_groups = ["Products", "Services"]
    
    for group in required_groups:
        if not frappe.db.exists("Item Group", group):
            frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group,
                "is_group": 0,
                "parent_item_group": "All Item Groups"
            }).insert()

def link_item_tax_template(item, company, vat_rate, is_exempt=False):
    """
    Link the appropriate tax template to an item based on VAT rate
    
    Args:
        item: Item document
        company: Company for which to find tax templates
        vat_rate: VAT rate for the item
        is_exempt: Whether the item is exempt from VAT
    """
    if not company:
        return
    
    # Map VAT rates to likely template names (adjust as needed)
    template_map = {
        19: "Cyprus VAT 19%",
        9: "Cyprus VAT 9%",
        5: "Cyprus VAT 5%",
        0: "Zero Rated" if not is_exempt else "Exempt"
    }
    
    template_name = template_map.get(vat_rate)
    
    if not template_name:
        return
    
    # Try to find the item tax template
    templates = frappe.get_all(
        "Item Tax Template",
        filters={"name": ["like", f"%{template_name}%"], "company": company},
        fields=["name"]
    )
    
    if not templates:
        return
    
    # Link the template to the item
    try:
        item_with_taxes = frappe.get_doc("Item", item.name)
        
        # Add the tax template to item taxes table
        item_with_taxes.append("taxes", {
            "item_tax_template": templates[0].name,
            "valid_from": frappe.utils.nowdate(),
            "company": company
        })
        
        item_with_taxes.save()
    except Exception:
        # If it fails, don't stop the process
        pass