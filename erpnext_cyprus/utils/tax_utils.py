import frappe
from frappe import _

def get_tax_accounts(company):
    """
    Get the necessary Cyprus tax accounts using exact account_name matches
    """
    accounts = {}
    missing_accounts = []
    found_accounts = []
    
    # Define the accounts we need by name
    required_accounts = {
        "vat": "VAT",
        "oss_vat": "OSS VAT"
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

def setup_purchase_tax_templates(company):
    """
    Set up Cyprus-specific purchase tax templates
    """
    
    # First remove the existing template called "Cyprus Tax"
    existing_template = frappe.db.exists("Purchase Taxes and Charges Template",
        {"title": "Cyprus Tax", "company": company})
    if existing_template:   
        frappe.delete_doc("Purchase Taxes and Charges Template", existing_template)

    templates_created = []
    
    # First ensure we have the required accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific purchase tax templates - one per use case
    cyprus_purchase_tax_templates = [        
        # EU services template
        {
            "title": "Reverse Charge",
            "company": company,
            "description": "Purchases eligible for reverse charge VAT",
            "taxes": [
                {
                    "account_head": tax_accounts["vat"],
                    "description": "Reverse Charge VAT",
                    "rate": 19,
                    "add_deduct_tax": "Add"
                },
                {
                    "account_head": tax_accounts["vat"],
                    "description": "Reverse Charge VAT",
                    "rate": 19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # Zero-rated purchases
        {
            "title": "Zero-Rated",
            "company": company,
            "description": "For zero-rated or exempt purchases",
            "taxes": []
        },        
        # Domestic purchase templates
        {
            "title": "Standard Domestic",
            "company": company,
            "description": "For ordinary purchases from local (Cypriot) suppliers where the supplier charges VAT at the standard rate",
            "taxes": [
                {
                    "account_head": tax_accounts["vat"],
                    "description": "VAT",
                    "rate": 19,
                    "add_deduct_tax": "Add"
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

def setup_sales_tax_templates(company):
    """
    Set up Cyprus-specific sales tax templates
    """
    templates_created = []

    # First remove the existing template called "Cyprus Tax"
    existing_template = frappe.db.exists("Sales Taxes and Charges Template",
        {"title": "Cyprus Tax", "company": company})
    if existing_template:
        frappe.delete_doc("Sales Taxes and Charges Template", existing_template)
    
    # First ensure we have the required accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific sales tax templates - one per use case
    cyprus_sales_tax_templates = [        
        {
            "title": "Standard Domestic",
            "company": company,
            "description": "For local sales with standard VAT.",
            "taxes": [
                {
                    "account_head": tax_accounts["vat"],
                    "description": "VAT",
                    "rate": 19
                }
            ]
        },
        {
            "title": "Zero-Rated",
            "company": company,
            "description": "For export sales where VAT is not charged.",
            "taxes": []
        },
        {
            "title": "Out-of-Scope",
            "company": company,
            "description": "For sales out of scope of VAT.",
            "taxes": []
        }
    ]
    
    # Create country-specific OSS digital services templates
    eu_vat_rates = get_eu_vat_rates()
    for country, vat_rate in eu_vat_rates.items():
        # Skip Cyprus as it uses domestic templates
        if country == "Cyprus":
            continue
            
        # Create the OSS template for this country
        oss_template = {
            "title": f"OSS Digital Services - {country} ({vat_rate}%)",
            "company": company,
            "description": f"Digital services to consumers in {country} (OSS)",
            "taxes": [
                {
                    "account_head": tax_accounts["oss_vat"],
                    "description": f"OSS VAT {country} {vat_rate}%",
                    "rate": vat_rate
                }
            ]
        }
        cyprus_sales_tax_templates.append(oss_template)
    
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

def setup_item_tax_templates(company):
    """
    Set up Cyprus-specific item tax templates for different VAT rates
    """

    # First remove the existing template called "Cyprus Tax"
    existing_template = frappe.db.exists("Item Tax Template",
        {"title": "Cyprus Tax", "company": company})
    if existing_template:
        frappe.delete_doc("Item Tax Template", existing_template)
        
    templates_created = []
    
    # Get the tax accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Extract the full account names for use in item tax templates
    vat_account = tax_accounts["vat"]
    
    # Define the Cyprus-specific item tax templates
    cyprus_item_tax_templates = [
        {
            "title": "Cyprus Standard",
            "taxes": [
                {
                    "tax_type": vat_account,
                    "tax_rate": 19
                }
            ]
        },
        {
            "title": "Cyprus Reduced",
            "taxes": [
                {
                    "tax_type": vat_account,
                    "tax_rate": 9
                }
            ]
        },
        {
            "title": "Cyprus Super Reduced",
            "taxes": [
                {
                    "tax_type": vat_account,
                    "tax_rate": 5
                }
            ]
        },
        {
            "title": "Zero Rated",
            "taxes": [
                {
                    "tax_type": vat_account,
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

def setup_tax_rules(company):
    """
    Set up Cyprus-specific tax rules for automatic tax template selection
    """
    rules_created = []
    
    # Get the actual template names first (since they include company abbreviations)
    template_names = {}
    
    # Get sales tax templates
    sales_templates = frappe.get_all(
        "Sales Taxes and Charges Template",
        filters={"company": company},
        fields=["name", "title"]
    )
    for template in sales_templates:
        template_names[template.title] = template.name
    
    # Get purchase tax templates
    purchase_templates = frappe.get_all(
        "Purchase Taxes and Charges Template",
        filters={"company": company},
        fields=["name", "title"]
    )
    for template in purchase_templates:
        template_names[template.title] = template.name
    
    # Debug - show what was found
    frappe.msgprint(f"Found {len(template_names)} tax templates for company {company}")
    
    # Initialize tax rules list
    tax_rules = []
    
    # Get EU VAT rates to create country-specific digital services rules
    eu_vat_rates = get_eu_vat_rates()
    
    # First add individual country rules for digital services
    for country, vat_rate in eu_vat_rates.items():
        if country == "Cyprus":
            # For Cyprus, use the standard template
            continue
            
        template_title = f"OSS Digital Services - {country} ({vat_rate}%)"
        template_name = template_names.get(template_title)
        
        if template_name:
            rule = {
                "doctype": "Tax Rule",
                "tax_type": "Sales",
                "customer_group": "Individual", 
                "billing_country": country,
                "sales_tax_template": template_name,
                "priority": 2,
                "use_for_shopping_cart": 1
            }
            tax_rules.append(rule)
    
    # Then add the standard rules    
    standard_rules = [
        # Default domestic rule
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            "billing_country": "Cyprus",
            "sales_tax_template": template_names.get("Standard Domestic"),
            "priority": 2,
            "use_for_shopping_cart": 1
        },
        # EU B2B and other countries
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            "sales_tax_template": template_names.get("Zero-Rated"),
            "priority": 1,
            "use_for_shopping_cart": 1
        },
        
        # PURCHASE RULES
        # Domestic purchases rule
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            "billing_country": "Cyprus",
            "purchase_tax_template": template_names.get("Standard Domestic"),
            "priority": 3
        },
        # EU commercial services rule
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            "billing_country": "EU",
            "purchase_tax_template": template_names.get("Reverse Charge"),
            "priority": 2
        },        
        # Zero-rated purchases are handled by the default template
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            "purchase_tax_template": template_names.get("Zero-Rated"),
            "priority": 1,
            "use_for_shopping_cart": 1
        },
    ]
    
    # Combine all rules
    tax_rules.extend(standard_rules)
    
    # Create each tax rule if it doesn't already exist
    for rule_data in tax_rules:
        # Add company to rule data
        rule_data["company"] = company
        
        # Check for existing rule with similar criteria
        filters = {
            "tax_type": rule_data["tax_type"],
            "company": company,
            "priority": rule_data["priority"]
        }
        
        if "billing_country" in rule_data:
            filters["billing_country"] = rule_data["billing_country"]
            
        if "customer_group" in rule_data:
            filters["customer_group"] = rule_data["customer_group"]
            
        existing_rule = frappe.db.exists("Tax Rule", filters)
        
        if not existing_rule:
            # Special handling for EU country group
            if rule_data.get("billing_country") == "EU":
                # Create rules for each EU country
                eu_countries = get_eu_countries()
                for country in eu_countries:
                    country_rule = rule_data.copy()
                    country_rule["billing_country"] = country
                    
                    # Create the rule
                    try:
                        new_rule = frappe.get_doc(country_rule)
                        new_rule.insert()
                        rules_created.append(f"{country_rule['tax_type']} - {country} - Priority {country_rule['priority']}")
                        frappe.db.commit()
                    except Exception as e:
                        frappe.log_error(f"Error creating tax rule for {country}: {str(e)}")
            else:
                # Create the rule
                try:
                    new_rule = frappe.get_doc(rule_data)
                    new_rule.insert()
                    rules_created.append(f"{rule_data['tax_type']} - {rule_data.get('billing_country', 'Any')} - Priority {rule_data['priority']}")
                    frappe.db.commit()
                except Exception as e:
                    frappe.log_error(f"Error creating tax rule: {str(e)}")
    
    return rules_created

def get_eu_vat_rates():
    """
    Return a dictionary of EU country standard VAT rates for OSS
    Source: European Commission, rates as of 2023
    """
    return {
        "Austria": 20,
        "Belgium": 21,
        "Bulgaria": 20,
        "Croatia": 25,
        "Czech Republic": 21,
        "Denmark": 25,
        "Estonia": 22,
        "Finland": 24,
        "France": 20,
        "Germany": 19,
        "Greece": 24,
        "Hungary": 27,
        "Ireland": 23,
        "Italy": 22,
        "Latvia": 21,
        "Lithuania": 21,
        "Luxembourg": 17,
        "Malta": 18,
        "Netherlands": 21,
        "Poland": 23,
        "Portugal": 23,
        "Romania": 19,
        "Slovakia": 20,
        "Slovenia": 22,
        "Spain": 21,
        "Sweden": 25
    }

def get_eu_countries():
    """Return a list of EU countries"""
    return list(get_eu_vat_rates().keys())
