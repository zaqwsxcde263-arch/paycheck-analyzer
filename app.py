import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "paycheck.db")

ALLOWED_CURRENCIES = ["USD", "RUB", "BYN", "EUR", "JPY"]

# Simple example rates: how much of each currency you get for 1 USD.
# Adjust these manually if you want more accurate or current values.
CURRENCY_RATES = {
    "USD": 1.0,
    "EUR": 0.92,
    "RUB": 90.0,
    "BYN": 3.2,
    "JPY": 150.0,
}


def create_app() -> Flask:
    app = Flask(__name__)
    # In production, override this with an environment variable
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-change-me")
    app.config["DATABASE"] = DB_PATH

    ensure_database(app)

    @app.context_processor
    def inject_currency_helpers():
        selected = get_selected_currency()
        return {
            "currencies": ALLOWED_CURRENCIES,
            "selected_currency": selected,
            "format_money": lambda amount: format_money(amount, selected),
        }

    @app.route("/")
    def index():
        return redirect(url_for("dashboard"))

    @app.route("/set-currency", methods=["POST"])
    def set_currency():
        currency = request.form.get("currency")
        if currency in ALLOWED_CURRENCIES:
            session["currency"] = currency
        else:
            flash("Unsupported currency selected.", "error")
        return redirect(request.referrer or url_for("dashboard"))

    @app.route("/expenses/new", methods=["GET", "POST"])
    def add_expenses():
        conn = get_db(app)
        categories = conn.execute(
            "SELECT id, name FROM categories ORDER BY name"
        ).fetchall()

        if not categories:
            flash("Please create at least one category before adding expenses.", "error")
            return redirect(url_for("manage_categories"))

        errors = []
        form_items = []
        date_value = datetime.today().strftime("%Y-%m-%d")

        if request.method == "POST":
            date_str = request.form.get("date", "").strip()
            products = request.form.getlist("product[]")
            category_ids = request.form.getlist("category_id[]")
            quantities = request.form.getlist("quantity[]")
            prices = request.form.getlist("price[]")

            # Validate date
            try:
                datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                errors.append("Date must be in format YYYY-MM-DD.")

            date_value = date_str

            valid_items = []

            for idx, (product, cat_id, qty, price) in enumerate(
                zip(products, category_ids, quantities, prices), start=1
            ):
                product = (product or "").strip()
                cat_id = (cat_id or "").strip()
                qty = (qty or "").strip()
                price = (price or "").strip()

                # Preserve form data
                form_items.append(
                    {
                        "product": product,
                        "category_id": cat_id,
                        "quantity": qty,
                        "price": price,
                    }
                )

                # Skip completely empty rows
                if not any([product, cat_id, qty, price]):
                    continue

                row_prefix = f"Row {idx}: "

                if not product:
                    errors.append(row_prefix + "Product name is required.")

                try:
                    cat_id_int = int(cat_id)
                except (TypeError, ValueError):
                    errors.append(row_prefix + "Category is required.")
                    cat_id_int = None

                try:
                    qty_int = int(qty)
                    if qty_int <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(row_prefix + "Quantity must be a positive integer.")
                    qty_int = None

                try:
                    price_float = float(price)
                    if price_float <= 0:
                        raise ValueError
                except (TypeError, ValueError):
                    errors.append(row_prefix + "Price must be a positive number.")
                    price_float = None

                if (
                    product
                    and cat_id_int is not None
                    and qty_int is not None
                    and price_float is not None
                ):
                    valid_items.append(
                        {
                            "product": product,
                            "category_id": cat_id_int,
                            "quantity": qty_int,
                            "price": price_float,
                        }
                    )

            if not valid_items and not errors:
                errors.append("Please fill at least one item row.")

            if not errors and valid_items:
                with conn:
                    conn.executemany(
                        """
                        INSERT INTO expenses (date, product, category_id, quantity, unit_price)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        [
                            (
                                date_value,
                                item["product"],
                                item["category_id"],
                                item["quantity"],
                                item["price"],
                            )
                            for item in valid_items
                        ],
                    )

                flash(f"Successfully added {len(valid_items)} expense item(s).", "success")
                return redirect(url_for("dashboard"))

        # Initial render or re-render with errors
        if not form_items:
            # Provide a few empty rows by default
            form_items = [
                {"product": "", "category_id": "", "quantity": "", "price": ""}
                for _ in range(3)
            ]

        return render_template(
            "add_expenses.html",
            categories=categories,
            errors=errors,
            items=form_items,
            date_value=date_value,
        )

    @app.route("/categories", methods=["GET", "POST"])
    def manage_categories():
        conn = get_db(app)
        errors = []

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            description = (request.form.get("description") or "").strip()

            if not name:
                errors.append("Category name is required.")
            else:
                try:
                    with conn:
                        conn.execute(
                            "INSERT INTO categories (name, description) VALUES (?, ?)",
                            (name, description or None),
                        )
                    flash(f"Category '{name}' created.", "success")
                    return redirect(url_for("manage_categories"))
                except sqlite3.IntegrityError:
                    errors.append("Category with this name already exists.")

        categories = conn.execute(
            "SELECT id, name, description FROM categories ORDER BY name"
        ).fetchall()

        return render_template(
            "categories.html",
            categories=categories,
            errors=errors,
        )

    @app.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
    def edit_category(category_id: int):
        conn = get_db(app)
        category = conn.execute(
            "SELECT id, name, description FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        if category is None:
            flash("Category not found.", "error")
            return redirect(url_for("manage_categories"))

        errors = []

        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            description = (request.form.get("description") or "").strip()

            if not name:
                errors.append("Category name is required.")
            else:
                try:
                    with conn:
                        conn.execute(
                            """
                            UPDATE categories
                            SET name = ?, description = ?
                            WHERE id = ?
                            """,
                            (name, description or None, category_id),
                        )
                    flash("Category updated.", "success")
                    return redirect(url_for("manage_categories"))
                except sqlite3.IntegrityError:
                    errors.append("Category with this name already exists.")

        return render_template(
            "category_edit.html",
            category=category,
            errors=errors,
        )

    @app.route("/categories/<int:category_id>/delete", methods=["POST"])
    def delete_category(category_id: int):
        conn = get_db(app)

        usage = conn.execute(
            "SELECT COUNT(*) AS cnt FROM expenses WHERE category_id = ?", (category_id,)
        ).fetchone()

        if usage["cnt"] > 0:
            flash("Cannot delete category that is used by expenses.", "error")
        else:
            with conn:
                conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            flash("Category deleted.", "success")

        return redirect(url_for("manage_categories"))

    @app.route("/dashboard")
    def dashboard():
        conn = get_db(app)

        monthly = conn.execute(
            """
            SELECT strftime('%Y-%m', date) AS period,
                   SUM(quantity * unit_price) AS total
            FROM expenses
            GROUP BY period
            ORDER BY period
            """
        ).fetchall()

        weekly = conn.execute(
            """
            SELECT strftime('%Y-%W', date) AS period,
                   SUM(quantity * unit_price) AS total
            FROM expenses
            GROUP BY period
            ORDER BY period
            """
        ).fetchall()

        by_category = conn.execute(
            """
            SELECT c.name AS category,
                   SUM(e.quantity * e.unit_price) AS total
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            GROUP BY c.id, c.name
            ORDER BY total DESC
            """
        ).fetchall()

        total_spent_row = conn.execute(
            "SELECT SUM(quantity * unit_price) AS total FROM expenses"
        ).fetchone()
        total_spent = total_spent_row["total"] or 0.0

        latest_date_row = conn.execute(
            "SELECT MAX(date) AS last_date FROM expenses"
        ).fetchone()
        last_date = latest_date_row["last_date"]

        return render_template(
            "dashboard.html",
            monthly=monthly,
            weekly=weekly,
            by_category=by_category,
            total_spent=total_spent,
            last_date=last_date,
        )

    @app.route("/products/trends")
    def product_trends():
        conn = get_db(app)

        products = conn.execute(
            "SELECT DISTINCT product FROM expenses ORDER BY product"
        ).fetchall()

        product_name = request.args.get("product") or None
        trend_points = []

        if product_name:
            trend_points = conn.execute(
                """
                SELECT date, unit_price
                FROM expenses
                WHERE product = ?
                ORDER BY date
                """,
                (product_name,),
            ).fetchall()

        return render_template(
            "product_trends.html",
            products=products,
            selected_product=product_name,
            trend_points=trend_points,
        )

    return app


def get_db(app: Flask) -> sqlite3.Connection:
    conn = getattr(app, "_database", None)
    if conn is None:
        conn = sqlite3.connect(app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        app._database = conn
    return conn


def ensure_database(app: Flask) -> None:
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True) if os.path.dirname(
        app.config["DATABASE"]
    ) else None
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            product TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_selected_currency() -> str:
    currency = session.get("currency") or "USD"
    if currency not in ALLOWED_CURRENCIES:
        currency = "USD"
        session["currency"] = currency
    return currency


def convert_amount(amount: float, target_currency: str) -> float:
    if amount is None:
        return 0.0
    rate = CURRENCY_RATES.get(target_currency, 1.0)
    return round(amount * rate, 2)


def format_money(amount: float, currency: str) -> str:
    converted = convert_amount(amount or 0.0, currency)
    return f"{converted:,.2f} {currency}"


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

