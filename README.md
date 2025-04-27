# ERPNext Cyprus

ERPNext extension for companies in Cyprus.

## Features

- Cyprus-specific tax compliance
- VAT reporting for Cyprus (standard VAT returns, MOSS, and VIES statements)
- Localized accounting features
- Additional reports for Cyprus regulatory requirements

## Installation

```bash
bench get-app https://github.com/your-organization/erpnext_cyprus
bench --site your-site.local install-app erpnext_cyprus
```

## Requirements

- ERPNext v15

## Tax Account Setup

The app automatically configures the following tax-related components:

### Tax Accounts
- **VAT** - Standard account for Cyprus VAT operations
- **OSS VAT** - For Mini One Stop Shop reporting for B2C digital services

### Tax Templates
- **Purchase Tax Templates**: 
  - Reverse Charge (19% VAT for EU acquisitions)
  - Standard Domestic (19% VAT)
  - Zero-Rated (for exempt purchases)

- **Sales Tax Templates**:
  - Standard Domestic (19% VAT)
  - Zero-Rated (for exports)
  - Out-of-Scope (for non-VAT sales)
  - OSS templates for each EU country with country-specific VAT rates

- **Item Tax Templates**:
  - Cyprus Standard 19%
  - Cyprus Reduced 9%
  - Cyprus Super Reduced 5%
  - Zero Rated
  - Exempt

### Tax Rules
Automatically applies correct tax templates based on:
- Customer/supplier country
- Whether the transaction is B2B or B2C
- Type of goods/services

### Item Groups
- Professional Services
- Digital Services

These are used to differentiate between goods and services for proper VAT reporting in boxes 8A/8B and 11A/11B of the VAT Return.

## Documentation

Available documentation:

- [Cyprus VAT Return Guide](documentation/cyprus_vat_return.md) - How to prepare and submit Cyprus VAT returns
- [VAT Statement Guide](documentation/vat_statement.md) - How to properly mark transactions for accurate VAT reporting
- [MOSS VAT Returns Guide](documentation/moss_vat_returns.md) - Guide for Mini One Stop Shop VAT reporting for digital services
- [VIES Statement Guide](documentation/vies_statement.md) - How to properly record and report EU B2B transactions

## Support

For issues and feature requests, please create an issue on the [GitHub repository](https://github.com/phalouvas/erpnext_cyprus/issues).

## License

GPL-3.0