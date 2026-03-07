## Paycheck Analyzer

Simple web application for manually tracking paycheck items and analyzing costs over time.

### Features

- **Manual data entry**: Add paycheck items one by one with required fields: date, product, category, items quantity, and price per item.
- **Dashboards**:
  - **By month**: Total spending aggregated per month.
  - **By category**: Total spending per category.
  - **By week**: Total spending per week.
  - **Product cost trends**: Price history and change per product over time.
- **Global currency selector**: View all costs in one of the supported currencies: USD, RUB, BYN, EUR, JPY.
- **Validation**: Server-side validation for all required fields and value ranges.

All monetary values are stored internally in a base currency and converted on the fly for display.

### Requirements

- Python 3.10+ recommended
- SQLite (bundled with Python via the `sqlite3` module)

### Installation

1. **Create and activate a virtual environment (recommended)**:

```bash
cd /home/shubinds/Projects
python -m venv venv
source venv/bin/activate
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

### Running the application

From the project directory:

```bash
python app.py
```

Then open your browser and visit:

```text
http://127.0.0.1:5000/
```

### Usage notes

- **Currency**: Use the currency selector in the top-right of the navigation bar to set the global display currency. All entered prices are assumed to be in that currency; dashboards convert totals based on simple built-in exchange rates.
- **Required fields**: Date, product name, category, items quantity, and price per item must be provided for each paycheck item.
- **Validation**:
  - Date must be a valid calendar date.
  - Quantity must be a positive integer.
  - Price must be a positive number.

You can extend this project by:

- Importing data from CSV files.
- Replacing the static exchange rates with live rates from an API.
- Adding authentication and multi-user support.

