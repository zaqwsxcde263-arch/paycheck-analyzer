## Paycheck Analyzer

A small web application to manually track paycheck items and analyze spending by month, by category, and by week. It also shows product price changes over time and supports a global currency selector.

### Tech stack

- **Language**: Python
- **Framework**: Flask
- **Database**: SQLite (file `paycheck.db` in the project root)

### Features

- **Manual data entry**
  - Enter a paycheck date once and add many items (rows) in a single form.
  - Each item has: date (shared for the form), product name, category, quantity, and price-per-item.
  - Server-side validation for every item:
    - Product name required.
    - Category required.
    - Quantity must be a positive integer.
    - Price must be a positive number.

- **Categories**
  - Separate pages to create, edit, and delete categories.
  - Each item in the paycheck form has a category selector populated from the categories you define.

- **Dashboards**
  - Overview dashboard:
    - Total spent (in the currently selected currency).
    - Last transaction date.
    - Chart: total by month.
    - Chart: total by week.
    - Chart: total by category (overall).
  - Product trends:
    - Select a product and see how its per-item price has changed over time.

- **Currency selector**
  - Global currency selector in the top navigation.
  - Available currencies: **USD, RUB, BYN, EUR, JPY**.
  - All values are stored internally in a base currency (treated as USD) and converted for display.

### Installation

1. **Create and activate a virtual environment** (recommended):

   ```bash
   cd paycheck-analyzer
   python -m venv .venv
   source .venv/bin/activate  # on Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:

   ```bash
   python app.py
   ```

4. Open the app in a browser:

   - `http://localhost:5000`

### Usage workflow

1. **Define categories**
   - Go to `Categories` in the top navigation.
   - Create categories such as `Groceries`, `Rent`, `Transport`, etc.

2. **Add paycheck items**
   - Go to `Add expenses`.
   - Set the paycheck date.
   - Fill in as many product rows as you need in a single form:
     - Product (name)
     - Category (select from the categories you created)
     - Quantity (items quantity)
     - Price (per item)
   - Use **“Add another item”** to insert more rows.
   - Submit the form; invalid rows will be reported with detailed messages.

3. **View dashboards**
   - Go to `Dashboard` to see:
     - Month-by-month totals.
     - Week-by-week totals.
     - Overall totals by category.

4. **Track product cost changes**
   - Go to `Product cost changes`.
   - Select a product name and view a line chart of its price-per-item over time.

5. **Change currency**
   - Use the currency selector in the top navigation.
   - This selection is global for the session; you do not need to set currency per item.

### Notes

- Default secret key and currency rates are suitable for local development only. For production use, set the `SECRET_KEY` environment variable and adjust `CURRENCY_RATES` in `app.py` as needed.
- The SQLite database (`paycheck.db`) is created automatically on first run.

