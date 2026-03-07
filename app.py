from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple

from flask import Flask, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


SUPPORTED_CURRENCIES = ["USD", "RUB", "BYN", "EUR", "JPY"]
BASE_CURRENCY = "USD"

# Rates are expressed as: 1 USD = rate in target currency
EXCHANGE_RATES: Dict[str, Decimal] = {
    "USD": Decimal("1.0"),
    "EUR": Decimal("0.92"),
    "RUB": Decimal("90.0"),
    "BYN": Decimal("3.2"),
    "JPY": Decimal("150.0"),
}


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///paycheck.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "change-me-in-production"

db = SQLAlchemy(app)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    product = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # price per item in base currency

    @property
    def total_base(self) -> Decimal:
        return Decimal(self.quantity) * Decimal(self.price)


def get_current_currency() -> str:
    currency = session.get("currency", BASE_CURRENCY)
    if currency not in SUPPORTED_CURRENCIES:
        currency = BASE_CURRENCY
    return currency


def convert_from_base(amount: Decimal, target_currency: str) -> Decimal:
    rate = EXCHANGE_RATES.get(target_currency, Decimal("1.0"))
    return (amount * rate).quantize(Decimal("0.01"))


def currency_symbol(currency: str) -> str:
    return {
        "USD": "$",
        "EUR": "€",
        "RUB": "₽",
        "BYN": "Br",
        "JPY": "¥",
    }.get(currency, currency)


@app.context_processor
def inject_globals():
    current_currency = get_current_currency()
    return {
        "supported_currencies": SUPPORTED_CURRENCIES,
        "current_currency": current_currency,
        "currency_symbol": currency_symbol(current_currency),
    }


@app.route("/")
def index():
    return redirect(url_for("add_expense"))


@app.route("/set-currency", methods=["POST"])
def set_currency():
    currency = request.form.get("currency", BASE_CURRENCY)
    if currency in SUPPORTED_CURRENCIES:
        session["currency"] = currency
    return redirect(request.referrer or url_for("index"))


@app.route("/add", methods=["GET", "POST"])
def add_expense():
    errors: Dict[str, str] = {}
    form_data = {
        "date": "",
        "product": "",
        "category": "",
        "quantity": "",
        "price": "",
    }

    if request.method == "POST":
        form_data["date"] = request.form.get("date", "").strip()
        form_data["product"] = request.form.get("product", "").strip()
        form_data["category"] = request.form.get("category", "").strip()
        form_data["quantity"] = request.form.get("quantity", "").strip()
        form_data["price"] = request.form.get("price", "").strip()

        # Validation
        # Date
        if not form_data["date"]:
            errors["date"] = "Date is required."
        else:
            try:
                parsed_date = datetime.strptime(form_data["date"], "%Y-%m-%d").date()
            except ValueError:
                errors["date"] = "Date must be in YYYY-MM-DD format."

        # Product
        if not form_data["product"]:
            errors["product"] = "Product name is required."

        # Category
        if not form_data["category"]:
            errors["category"] = "Category is required."

        # Quantity
        quantity_val = None
        if not form_data["quantity"]:
            errors["quantity"] = "Quantity is required."
        else:
            try:
                quantity_val = int(form_data["quantity"])
                if quantity_val <= 0:
                    errors["quantity"] = "Quantity must be a positive integer."
            except ValueError:
                errors["quantity"] = "Quantity must be an integer."

        # Price
        price_val = None
        if not form_data["price"]:
            errors["price"] = "Price is required."
        else:
            try:
                price_val = Decimal(form_data["price"])
                if price_val <= 0:
                    errors["price"] = "Price must be a positive number."
            except Exception:
                errors["price"] = "Price must be a valid number."

        if not errors:
            expense = Expense(
                date=parsed_date,
                product=form_data["product"],
                category=form_data["category"],
                quantity=quantity_val,
                price=price_val,
            )
            db.session.add(expense)
            db.session.commit()
            return redirect(url_for("add_expense"))

    return render_template("add_expense.html", errors=errors, form_data=form_data)


def _aggregate_summary() -> Tuple[List[Tuple[str, Decimal]], List[Tuple[str, Decimal]], List[Tuple[str, Decimal]]]:
    # By month (YYYY-MM)
    monthly = (
        db.session.query(
            func.strftime("%Y-%m", Expense.date).label("month"),
            func.sum(Expense.price * Expense.quantity).label("total"),
        )
        .group_by("month")
        .order_by("month")
        .all()
    )

    # By category
    categories = (
        db.session.query(
            Expense.category.label("category"),
            func.sum(Expense.price * Expense.quantity).label("total"),
        )
        .group_by(Expense.category)
        .order_by(Expense.category)
        .all()
    )

    # By week (ISO week number: YYYY-WW)
    weekly = (
        db.session.query(
            func.strftime("%Y", Expense.date).label("year"),
            func.strftime("%W", Expense.date).label("week"),
            func.sum(Expense.price * Expense.quantity).label("total"),
        )
        .group_by("year", "week")
        .order_by("year", "week")
        .all()
    )

    return monthly, categories, weekly


@app.route("/dashboard/summary")
def dashboard_summary():
    current_currency = get_current_currency()
    monthly, categories, weekly = _aggregate_summary()

    def convert_rows(rows, label_key):
        converted = []
        for row in rows:
            label = getattr(row, label_key)
            total_base = Decimal(row.total)
            total_converted = convert_from_base(total_base, current_currency)
            converted.append((label, total_converted))
        return converted

    monthly_data = convert_rows(monthly, "month")

    category_data = convert_rows(categories, "category")

    weekly_data = []
    for row in weekly:
        label = f"{row.year}-W{row.week}"
        total_base = Decimal(row.total)
        total_converted = convert_from_base(total_base, current_currency)
        weekly_data.append((label, total_converted))

    return render_template(
        "dashboard_summary.html",
        monthly_data=monthly_data,
        category_data=category_data,
        weekly_data=weekly_data,
    )


@app.route("/dashboard/product-trends")
def dashboard_product_trends():
    current_currency = get_current_currency()
    products = (
        db.session.query(Expense.product)
        .distinct()
        .order_by(Expense.product)
        .all()
    )
    product_names = [p.product for p in products]

    selected_product = request.args.get("product") or (product_names[0] if product_names else None)

    trend_rows: List[Dict] = []
    if selected_product:
        expenses = (
            Expense.query.filter_by(product=selected_product)
            .order_by(Expense.date.asc())
            .all()
        )
        previous_price = None
        for e in expenses:
            unit_price_converted = convert_from_base(Decimal(e.price), current_currency)
            total_converted = convert_from_base(e.total_base, current_currency)
            price_change = None
            if previous_price is not None:
                price_change = unit_price_converted - previous_price
            trend_rows.append(
                {
                    "date": e.date,
                    "quantity": e.quantity,
                    "unit_price": unit_price_converted,
                    "total": total_converted,
                    "price_change": price_change,
                }
            )
            previous_price = unit_price_converted

    return render_template(
        "dashboard_product_trends.html",
        products=product_names,
        selected_product=selected_product,
        trend_rows=trend_rows,
    )


def init_db():
    with app.app_context():
        db.create_all()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

