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

def get_cyprus_tax_accounts(company):
    """
    Get the necessary Cyprus tax accounts using exact account_name matches
    """
    accounts = {}
    missing_accounts = []
    found_accounts = []
    
    # Define the accounts we need by name
    required_accounts = {
        "vat_local_19": "VAT Cyprus Local (19%)",
        "vat_reduced_9": "VAT Cyprus Reduced (9%)",
        "vat_super_reduced_5": "VAT Cyprus Super Reduced (5%)",
        "intra_eu_acquisition": "Intra-EU Acquisition VAT",
        "reverse_charge_services": "Reverse Charge VAT B2B Services",
        "import_vat": "Import VAT Non-EU",
        "oss_vat": "OSS VAT Digital Services"
    }
    
    # Simple direct search for each account by exact account_name and company
    for key, account_name in required_accounts.items():
        # Only use the exact account_name and company
        account = frappe.db.get_value("Account", 
            {"account_name": account_name, "company": company}, "name")
        
        # Store result
        if account:
            accounts[key] = account
            found_accounts.append(f"{key}: {account_name} → {account}")
        else:
            missing_accounts.append(account_name)
            accounts[key] = None
    
    # Only show missing accounts in production - this is critical information
    if missing_accounts:
        frappe.msgprint(_("Could not find these tax accounts:") + "<br>" + "<br>".join(missing_accounts))
        return None
    
    return accounts

def setup_cyprus_purchase_tax_templates(company):
    """
    Set up Cyprus-specific purchase tax templates
    """
    templates_created = []
    
    # First ensure we have the required accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific purchase tax templates - one per use case
    cyprus_purchase_tax_templates = [        
        # Main domestic purchase template with all rates
        {
            "title": "Cyprus Purchase VAT (All Rates)",
            "company": company,
            "is_inter_state": 0,
            "tax_category": "Cyprus Standard",
            "description": "All Cyprus domestic purchase VAT rates",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "VAT 19%",
                    "rate": 19
                },
                {
                    "account_head": tax_accounts["vat_reduced_9"],
                    "description": "VAT 9%",
                    "rate": 0  # Default to 0, controlled by item tax templates
                },
                {
                    "account_head": tax_accounts["vat_super_reduced_5"],
                    "description": "VAT 5%",
                    "rate": 0  # Default to 0, controlled by item tax templates
                }
            ]
        },
        # EU acquisition template
        {
            "title": "EU Acquisition VAT 19%",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "EU B2B",
            "description": "For goods acquired from EU suppliers",
            "taxes": [
                {
                    "account_head": tax_accounts["intra_eu_acquisition"],
                    "description": "EU Acquisition VAT 19%",
                    "rate": 19,
                    "add_deduct_tax": "Add"
                },
                {
                    "account_head": tax_accounts["intra_eu_acquisition"],
                    "description": "Reverse EU Acquisition VAT 19%",
                    "rate": -19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # EU services template
        {
            "title": "EU Services Reverse Charge",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "EU B2C",  # Using EU B2C for this template
            "description": "For services from EU suppliers",
            "taxes": [
                {
                    "account_head": tax_accounts["reverse_charge_services"],
                    "description": "Reverse Charge VAT 19%",
                    "rate": 19,
                    "add_deduct_tax": "Add"
                },
                {
                    "account_head": tax_accounts["reverse_charge_services"],
                    "description": "Reverse Charge VAT 19% (Input)",
                    "rate": -19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # Non-EU import template
        {
            "title": "Non-EU Import VAT",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "Non-EU",
            "description": "For imports from outside the EU",
            "taxes": [
                {
                    "account_head": tax_accounts["import_vat"],
                    "description": "Import VAT 19%",
                    "rate": 19
                }
            ]
        },
        # Exempt purchases
        {
            "title": "Zero-Rated Purchase",
            "company": company,
            "is_inter_state": 0,
            "tax_category": "Exempt",
            "description": "For zero-rated or exempt purchases",
            "taxes": []
        },
        # Digital services
        {
            "title": "Digital Services Purchase",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "Digital Services",
            "description": "For digital services purchases",
            "taxes": [
                {
                    "account_head": tax_accounts["oss_vat"],
                    "description": "OSS VAT",
                    "rate": 19
                }
            ]
        }
    ]
    
    # Create each purchase tax template if it doesn't already exist
    for template_data in cyprus_purchase_tax_templates:
        existing_template = frappe.db.exists("Purchase Taxes and Charges Template", 
            {"title": template_data["title"], "company": company})
        
        if not existing_template:
            # Create the template
            new_template = frappe.get_doc({
                "doctype": "Purchase Taxes and Charges Template",
                "title": template_data["title"],
                "company": template_data["company"],
                "is_inter_state": template_data["is_inter_state"],
                "tax_category": template_data["tax_category"],
                "disabled": 0,
                "description": template_data["description"]
            })
            
            # Add the taxes
            for tax in template_data["taxes"]:
                new_template.append("taxes", {
                    "account_head": tax["account_head"],
                    "description": tax["description"],
                    "rate": tax["rate"],
                    "add_deduct_tax": tax.get("add_deduct_tax", "Add"),
                    "category": "Total",
                    "charge_type": "On Net Total"
                })
            
            new_template.insert()
            templates_created.append(template_data["title"])
            frappe.db.commit()
            
    return templates_created

def setup_cyprus_sales_tax_templates(company):
    """
    Set up Cyprus-specific sales tax templates
    """
    templates_created = []
    
    # First ensure we have the required accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific sales tax templates - one per use case
    cyprus_sales_tax_templates = [        
        # Main domestic sales template with all rates
        {
            "title": "Cyprus Sales VAT (All Rates)",
            "company": company,
            "is_inter_state": 0,
            "tax_category": "Cyprus Standard",
            "description": "All Cyprus domestic sales VAT rates",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "VAT 19%",
                    "rate": 19
                },
                {
                    "account_head": tax_accounts["vat_reduced_9"],
                    "description": "VAT 9%",
                    "rate": 0  # Default to 0, controlled by item tax templates
                },
                {
                    "account_head": tax_accounts["vat_super_reduced_5"],
                    "description": "VAT 5%",
                    "rate": 0  # Default to 0, controlled by item tax templates
                }
            ]
        },
        # EU B2B sales (reverse charge)
        {
            "title": "EU B2B Sales (Reverse Charge)",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "EU B2B",
            "description": "For VAT-registered businesses in EU (0% with reverse charge)",
            "taxes": []  # Zero-rated
        },
        # EU B2C sales (charge local VAT)
        {
            "title": "EU B2C Sales",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "EU B2C",
            "description": "For consumers in EU (with local VAT)",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "VAT 19%",
                    "rate": 19
                }
            ]
        },
        # Non-EU export sales
        {
            "title": "Non-EU Export",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "Non-EU",
            "description": "For exports outside the EU (zero-rated)",
            "taxes": []  # Zero-rated
        },
        # Digital services (OSS)
        {
            "title": "Digital Services EU (OSS)",
            "company": company,
            "is_inter_state": 1,
            "tax_category": "Digital Services",
            "description": "For digital services to EU consumers (OSS)",
            "taxes": [
                {
                    "account_head": tax_accounts["oss_vat"],
                    "description": "OSS VAT",
                    "rate": 19  # Default rate, can be overridden by item tax templates
                }
            ]
        },
        # Exempt sales
        {
            "title": "VAT Exempt Sales",
            "company": company,
            "is_inter_state": 0,
            "tax_category": "Exempt",
            "description": "For VAT-exempt goods and services",
            "taxes": []  # Zero-rated
        }
    ]
    
    # Create each sales tax template if it doesn't already exist
    for template_data in cyprus_sales_tax_templates:
        existing_template = frappe.db.exists("Sales Taxes and Charges Template", 
            {"title": template_data["title"], "company": company})
        
        if not existing_template:
            # Create the template
            new_template = frappe.get_doc({
                "doctype": "Sales Taxes and Charges Template",
                "title": template_data["title"],
                "company": template_data["company"],
                "is_inter_state": template_data["is_inter_state"],
                "tax_category": template_data["tax_category"],
                "disabled": 0,
                "description": template_data["description"]
            })
            
            # Add the taxes
            for tax in template_data["taxes"]:
                new_template.append("taxes", {
                    "account_head": tax["account_head"],
                    "description": tax["description"],
                    "rate": tax["rate"],
                    "add_deduct_tax": tax.get("add_deduct_tax", "Add"),
                    "category": "Total",
                    "charge_type": "On Net Total"
                })
            
            new_template.insert()
            templates_created.append(template_data["title"])
            frappe.db.commit()
            
    return templates_created

def setup_cyprus_item_tax_templates(company):
    """
    Set up Cyprus-specific item tax templates for different VAT rates
    """
    templates_created = []
    
    # Get the tax accounts
    tax_accounts = get_cyprus_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Extract the full account names for use in item tax templates
    vat_19_account = tax_accounts["vat_local_19"]
    vat_9_account = tax_accounts["vat_reduced_9"]
    vat_5_account = tax_accounts["vat_super_reduced_5"]
    
    # Define the Cyprus-specific item tax templates
    cyprus_item_tax_templates = [
        {
            "title": "Cyprus Standard 19%",
            "taxes": [
                {
                    "tax_type": vat_19_account,
                    "tax_rate": 19
                },
                {
                    "tax_type": vat_9_account,
                    "tax_rate": 0
                },
                {
                    "tax_type": vat_5_account,
                    "tax_rate": 0
                }
            ]
        },
        {
            "title": "Cyprus Reduced 9%",
            "taxes": [
                {
                    "tax_type": vat_19_account,
                    "tax_rate": 0
                },
                {
                    "tax_type": vat_9_account,
                    "tax_rate": 9
                },
                {
                    "tax_type": vat_5_account,
                    "tax_rate": 0
                }
            ]
        },
        {
            "title": "Cyprus Super Reduced 5%",
            "taxes": [
                {
                    "tax_type": vat_19_account,
                    "tax_rate": 0
                },
                {
                    "tax_type": vat_9_account,
                    "tax_rate": 0
                },
                {
                    "tax_type": vat_5_account,
                    "tax_rate": 5
                }
            ]
        },
        {
            "title": "Zero Rated",
            "taxes": [
                {
                    "tax_type": vat_19_account,
                    "tax_rate": 0
                }
            ]
        },
        {
            "title": "Exempt",
            "taxes": [
                {
                    "tax_type": vat_19_account,
                    "tax_rate": 0
                }
            ]
        }
    ]
    
    # Create each item tax template if it doesn't already exist
    for template_data in cyprus_item_tax_templates:
        existing_template = frappe.db.exists("Item Tax Template", 
            {"title": template_data["title"]})
        
        if not existing_template:
            # Create the template
            new_template = frappe.get_doc({
                "doctype": "Item Tax Template",
                "title": template_data["title"],
                "disabled": 0,
                "company": company  # Item tax templates should be company-specific
            })
            
            # Add the taxes
            for tax in template_data["taxes"]:
                new_template.append("taxes", {
                    "tax_type": tax["tax_type"],
                    "tax_rate": tax["tax_rate"]
                })
            
            try:
                new_template.insert()
                templates_created.append(template_data["title"])
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error creating item tax template {template_data['title']}: {str(e)}")
            
    return templates_created