# ERPNext Cyprus

ERPNext extension for companies in Cyprus. This application extends ERPNext functionality to support Cyprus-specific tax regulations, VAT reporting requirements, and business operations.

## Features

- Cyprus-specific tax compliance
  - VAT calculation based on Cyprus tax rates
  - Support for reverse charge mechanism
  - Automated tax calculations for local and EU transactions
- Comprehensive VAT reporting
  - Standard VAT returns for Cyprus Tax Department
  - MOSS VAT reporting for digital services
  - VIES statement for EU B2B transactions
- Localized accounting features
  - Cyprus-specific chart of accounts
  - Tax account templates
  - EU transaction handling
- Additional reports for Cyprus regulatory requirements
  - Intrastat reporting
  - Customer/supplier transaction summaries
  - EU sales and purchase listings

## Installation

```bash
# Get the app from the repository
bench get-app https://github.com/your-organization/erpnext_cyprus

# Install the app on your site
bench --site your-site.local install-app erpnext_cyprus

# Build assets and restart the server
bench build
bench restart
```

## Requirements

- Frappe Framework v15
- ERPNext v15
- A properly configured ERPNext site with Chart of Accounts

## Configuration

After installation, you'll need to:

1. Configure your company settings with proper Cyprus tax information
2. Set up VAT accounts (Output and Input)
3. Configure tax templates for various transaction types
4. Set up customer and supplier records with proper tax IDs

Refer to the documentation for detailed setup instructions.

## Usage

The app adds Cyprus-specific functionality to your ERPNext installation:

- Use the VAT Statement report for preparing VAT returns
- Generate VIES statements for EU B2B transactions
- Prepare MOSS VAT returns for digital services to EU consumers
- Access Cyprus-specific tax rates and account templates

## Documentation

Available documentation:

- [VAT Statement Guide](documentation/vat_statement.md) - How to properly mark transactions for accurate VAT reporting
- [MOSS VAT Returns Guide](documentation/moss_vat_returns.md) - Guide for Mini One Stop Shop VAT reporting for digital services
- [VIES Statement Guide](documentation/vies_statement.md) - How to properly record and report EU B2B transactions

## Support

For issues and feature requests, please create an issue on the [GitHub repository](https://github.com/phalouvas/erpnext_cyprus/issues).

## License

GPL-3.0