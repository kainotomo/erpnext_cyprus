import frappe
from frappe import _

def setup_cyprus_tax_categories():
    """
    Set up Cyprus-specific tax categories
    """
    tax_categories_created = []
    
    # Define the Cyprus-specific tax categories
    cyprus_tax_categories = [
        {
            "title": "Cyprus Standard",
            "description": "Default for all domestic transactions"
        },
        {
            "title": "EU B2B",
            "description": "For business customers in EU with valid VAT numbers"
        },
        {
            "title": "EU B2C",
            "description": "For consumers in EU countries"
        },
        {
            "title": "Non-EU",
            "description": "For customers outside the EU"
        },
        {
            "title": "Digital Services",
            "description": "For electronically supplied services to EU consumers"
        },
        {
            "title": "Exempt",
            "description": "For VAT-exempt transactions"
        }
    ]
    
    # Create each tax category if it doesn't already exist
    for category_data in cyprus_tax_categories:
        existing_category = frappe.db.get_value("Tax Category", 
            {"title": category_data["title"]}, "name")
        
        if not existing_category:
            new_category = frappe.get_doc({
                "doctype": "Tax Category",
                "title": category_data["title"],
                "is_exempt": category_data["title"] == "Exempt",
                "description": category_data["description"]
            })
            
            new_category.insert()
            tax_categories_created.append(category_data["title"])
            frappe.db.commit()
            
    return tax_categories_created