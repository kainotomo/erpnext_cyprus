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
        "vat_local_19": "VAT",
        "vat_reduced_9": "VAT",
        "vat_super_reduced_5": "VAT",
        "intra_eu_acquisition": "VAT",
        "reverse_charge_services": "VAT",
        "import_vat": "VAT",
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
    templates_created = []
    
    # First ensure we have the required accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific purchase tax templates - one per use case
    cyprus_purchase_tax_templates = [        
        # EU acquisition template
        {
            "title": "EU Acquisition VAT 19%",
            "company": company,
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
                    "rate": 19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # EU services template
        {
            "title": "EU Reverse Charge",
            "company": company,
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
                    "rate": 19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # Non-EU import template
        {
            "title": "Non-EU Import VAT",
            "company": company,
            "description": "For imports from outside the EU",
            "taxes": [
                {
                    "account_head": tax_accounts["import_vat"],
                    "description": "Import VAT 19%",
                    "rate": 19,
                    "add_deduct_tax": "Add"
                },
                {
                    "account_head": tax_accounts["import_vat"],
                    "description": "Import VAT 19% (Input)",
                    "rate": 19,
                    "add_deduct_tax": "Deduct"
                }
            ]
        },
        # Exempt purchases
        {
            "title": "Zero-Rated Purchase",
            "company": company,
            "description": "For zero-rated or exempt purchases",
            "taxes": []
        },        
        # Domestic purchase templates
        {
            "title": "Cyprus Purchase VAT",
            "company": company,
            "description": "For domestic purchases with VAT",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "Input VAT",
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
    
    # First ensure we have the required accounts
    tax_accounts = get_tax_accounts(company)
    if not tax_accounts:
        frappe.msgprint(_("Required tax accounts not found. Please set up the chart of accounts first."))
        return templates_created
    
    # Define the Cyprus-specific sales tax templates - one per use case
    cyprus_sales_tax_templates = [        
        {
            "title": "Cyprus Sales VAT",
            "company": company,
            "description": "All Cyprus domestic sales VAT rates",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "VAT 19%",
                    "rate": 19
                }
            ]
        },
        {
            "title": "EU B2B Sales (Reverse Charge)",
            "company": company,
            "description": "For VAT-registered businesses in EU (0% with reverse charge)",
            "taxes": []  # Zero-rated
        },
        {
            "title": "EU B2C Sales",
            "company": company,
            "description": "For consumers in EU (with local VAT)",
            "taxes": [
                {
                    "account_head": tax_accounts["vat_local_19"],
                    "description": "VAT 19%",
                    "rate": 19
                }
            ]
        },
        {
            "title": "Non-EU Export",
            "company": company,
            "description": "For exports outside the EU (zero-rated)",
            "taxes": []  # Zero-rated
        },
        {
            "title": "VAT Exempt Sales",
            "company": company,
            "description": "For VAT-exempt goods and services",
            "taxes": []  # Zero-rated
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
    templates_created = []
    
    # Get the tax accounts
    tax_accounts = get_tax_accounts(company)
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
                }
            ]
        },
        {
            "title": "Cyprus Reduced 9%",
            "taxes": [
                {
                    "tax_type": vat_9_account,
                    "tax_rate": 9
                }
            ]
        },
        {
            "title": "Cyprus Super Reduced 5%",
            "taxes": [
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
    cyprus_tax_rules = []
    
    # Get EU VAT rates to create country-specific digital services rules
    eu_vat_rates = get_eu_vat_rates()
    
    # First add individual country rules for digital services
    for country, vat_rate in eu_vat_rates.items():
        if country == "Cyprus":
            # For Cyprus, use the standard template
            continue
            
        country_code = country[:2].upper()
        template_title = f"OSS Digital Services - {country} ({vat_rate}%)"
        template_name = template_names.get(template_title)
        
        if template_name:
            rule = {
                "doctype": "Tax Rule",
                "tax_type": "Sales",
                "customer_group": "Individual", 
                "billing_country": country,
                "item_group": "Digital Services", # Re-enable this!
                "sales_tax_template": template_name,
                "priority": 10,  # HIGHEST priority - highest number
                "use_for_shopping_cart": 1
            }
            cyprus_tax_rules.append(rule)
    
    # Then add the standard rules    
    standard_rules = [
        # EU B2B - for all EU countries
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            "customer_group": "Commercial", 
            "billing_country": "EU",
            "sales_tax_template": template_names.get("EU B2B Sales (Reverse Charge)"),
            "priority": 8,
            "use_for_shopping_cart": 1
        },
        # EU B2C - non-digital (regular goods)
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            "customer_group": "Individual",
            "billing_country": "EU",  # Will be expanded to individual countries
            "sales_tax_template": template_names.get("EU B2C Sales"),
            "priority": 3,
            "use_for_shopping_cart": 1
        },
        # Non-EU exports (priority 4)
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            # No billing_country - applies to any country not matched by higher priority rules
            "sales_tax_template": template_names.get("Non-EU Export"),
            "priority": 4,
            "use_for_shopping_cart": 1
        },        
        # Default domestic rule
        {
            "doctype": "Tax Rule",
            "tax_type": "Sales",
            "billing_country": "Cyprus",
            "sales_tax_template": template_names.get("Cyprus Sales VAT (All Rates)"),
            "priority": 4,
            "use_for_shopping_cart": 1
        },
        
        # PURCHASE RULES - modified to use supplier_group instead of tax_category
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            "billing_country": "EU",
            "purchase_tax_template": template_names.get("EU Acquisition VAT 19%"),
            "priority": 1
        },
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            "billing_country": "EU",
            "item_group": "Services",
            "purchase_tax_template": template_names.get("EU Services Reverse Charge"),
            "priority": 2
        },
        {
            "doctype": "Tax Rule",
            "tax_type": "Purchase",
            # No tax_category reference - applies to any country not matched by higher priority rules
            "purchase_tax_template": template_names.get("Non-EU Import VAT"),
            "priority": 3
        }
    ]
    
    # Combine all rules
    cyprus_tax_rules.extend(standard_rules)
    
    # Create each tax rule if it doesn't already exist
    for rule_data in cyprus_tax_rules:
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
            
        if "supplier_group" in rule_data:
            filters["supplier_group"] = rule_data["supplier_group"]
            
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
        "Cyprus": 19,
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

def setup_item_groups():
    """
    Set up the required item groups for Cyprus tax rules
    """
    groups_created = []
    
    # Define the required item groups
    required_item_groups = [
        {
            "item_group_name": "Professional Services",
            "parent_item_group": "All Item Groups",
            "is_group": 1,
            "description": "These are expertise-driven services that involve specialized knowledge and skills, such as consulting, legal advice, marketing, IT support, and training. They often require direct interaction between the service provider and client, making them distinct from automated digital offerings."
        },
        {
            "item_group_name": "Digital Services",
            "parent_item_group": "All Item Groups",
            "is_group": 1,
            "description": "These are technology-based services provided online, including software licensing, cloud hosting, digital content delivery, e-learning, and automated solutions like SaaS (Software as a Service). Digital services are often subscription-based or pay-per-use and fall under specific VAT regulations, such as the OSS scheme for EU sales."
        }
    ]
    
    # Create each item group if it doesn't already exist
    for group_data in required_item_groups:
        existing_group = frappe.db.exists("Item Group", group_data["item_group_name"])
        
        if not existing_group:
            # Check if parent exists, default to "All Item Groups" if not
            parent_exists = frappe.db.exists("Item Group", group_data["parent_item_group"])
            parent_group = group_data["parent_item_group"] if parent_exists else "All Item Groups"
            
            # Create the item group
            new_group = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": group_data["item_group_name"],
                "parent_item_group": parent_group,
                "is_group": group_data["is_group"],
                "description": group_data["description"]
            })
            
            try:
                new_group.insert()
                groups_created.append(group_data["item_group_name"])
                frappe.db.commit()
            except Exception as e:
                frappe.log_error(f"Error creating item group {group_data['item_group_name']}: {str(e)}")
    
    return groups_created

def setup_cyprus_territories():
    """
    Set up territories needed for Cyprus VAT reporting (simplified structure)
    """
    territories_created = []
    
    # Define base required territories
    required_territories = [
        {
            "territory_name": "Cyprus",
            "parent_territory": "All Territories",
            "is_group": 0
        },
        {
            "territory_name": "EU",
            "parent_territory": "All Territories",
            "is_group": 0
        },
        {
            "territory_name": "Rest Of The World",
            "parent_territory": "All Territories",
            "is_group": 1
        }
    ]
    
    # Create territories if they don't exist
    for territory_data in required_territories:
        if not frappe.db.exists("Territory", territory_data["territory_name"]):
            territory = frappe.get_doc({
                "doctype": "Territory",
                "territory_name": territory_data["territory_name"],
                "parent_territory": territory_data["parent_territory"],
                "is_group": territory_data["is_group"]
            })
            territory.insert(ignore_permissions=True)
            territories_created.append(territory_data["territory_name"])
    
    return territories_created